#!/usr/bin/env python3
"""
AutoEdit TikTok Generator — Standalone script.
NO server needed. NO tokens needed. Just ffmpeg + PIL.
Creates a viral TikTok-style video from text + colors.

Usage:
    python3 tiktok-gen.py "Your caption here" output.mp4
"""
import subprocess, tempfile, shutil, os, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_background(w, h, duration, fps=30):
    """Generate animated gradient frames."""
    frames_dir = tempfile.mkdtemp(prefix="bg_")
    total_frames = int(duration * fps)
    
    colors = [
        (255, 0, 80),   # Pink
        (0, 255, 200),  # Cyan
        (255, 200, 0),  # Gold
        (150, 0, 255),  # Purple
    ]
    
    for i in range(total_frames):
        progress = i / total_frames
        # Interpolate between colors
        idx = int(progress * (len(colors) - 1))
        t = (progress * (len(colors) - 1)) - idx
        c1, c2 = colors[idx], colors[min(idx + 1, len(colors) - 1)]
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        
        # Add noise/pattern
        img = Image.new("RGB", (w, h), (r, g, b))
        draw = ImageDraw.Draw(img)
        
        # Random circles
        for _ in range(5):
            cx = int(random.random() * w)
            cy = int(random.random() * h)
            rad = int(random.random() * 200 + 100)
            rr = min(255, r + int(random.random() * 40 - 20))
            gg = min(255, g + int(random.random() * 40 - 20))
            bb = min(255, b + int(random.random() * 40 - 20))
            draw.ellipse([cx-rad, cy-rad, cx+rad, cy+rad], fill=(rr, gg, bb))
        
        img.save(f"{frames_dir}/f{i:05d}.png")
    
    return frames_dir, fps

def generate_caption_frames(w, h, duration, fps, text, style="tiktok"):
    """Generate caption overlay frames with PIL."""
    frames_dir = tempfile.mkdtemp(prefix="cap_")
    total_frames = int(duration * fps)
    
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    font = ImageFont.truetype(font_path, min(h // 10, 90))
    
    for i in range(total_frames):
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        x = (w - tw) // 2
        y = int(h * 0.72)
        
        # BOUNCE animation
        bounce = abs((i / (fps * 0.5)) % 2 - 1) * 20
        y += int(bounce)
        
        # Glow
        for dx, dy in [(j, k) for j in range(-8, 9, 2) for k in range(-8, 9, 2)]:
            draw.text((x+dx, y+dy), text, font=font, fill=(255, 50, 150, 40))
        
        # Pill background
        draw.rounded_rectangle([x-30, y-18, x+tw+30, y+th+18], radius=24, fill=(0, 0, 0, 170))
        
        # Outline + text
        for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
            draw.text((x+dx, y+dy), text, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        # Watermark
        wm = ImageFont.truetype(font_path, 24)
        draw.text((w - 120, 20), "AutoEdit", font=wm, fill=(255, 255, 255, 180))
        
        overlay.save(f"{frames_dir}/f{i:05d}.png")
    
    return frames_dir, fps

def generate_audio(text, output_path):
    """Generate speech audio with macOS say + ffmpeg."""
    import tempfile
    fd, aiff = tempfile.mkstemp(suffix=".aiff")
    os.close(fd)
    r = subprocess.run(["say", "-v", "Samantha", "-o", aiff, text], capture_output=True, timeout=15)
    if r.returncode != 0:
        # Create silent audio as fallback
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "8",
                       "-c:a", "aac", "-b:a", "128k", output_path], capture_output=True, timeout=15)
    else:
        subprocess.run(["ffmpeg", "-y", "-i", aiff, "-c:a", "aac", "-b:a", "128k", output_path],
                       capture_output=True, timeout=15)
    if os.path.exists(aiff):
        os.remove(aiff)
    return output_path

def create_tiktok_video(text, output_path, duration=8):
    """Main function: create a TikTok-style video."""
    w, h = 1080, 1920
    fps = 30
    
    print(f"🎬 AutoEdit TikTok Generator")
    print(f"   Text: {text}")
    print(f"   Duration: {duration}s")
    print(f"   Output: {output_path}")
    print()
    
    # 1. Generate background
    print("1. Generating animated background...")
    bg_dir, fps = generate_background(w, h, duration, fps)
    bg_video = tempfile.mktemp(suffix="_bg.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", f"{bg_dir}/f_%05d.png",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        bg_video
    ], capture_output=True, timeout=60)
    shutil.rmtree(bg_dir, ignore_errors=True)
    print("   ✅ Background done")
    
    # 2. Generate audio
    print("2. Generating speech...")
    audio = tempfile.mktemp(suffix=".m4a")
    generate_audio(text, audio)
    print("   ✅ Audio done")
    
    # 3. Mix background + audio
    print("3. Mixing video + audio...")
    base_video = tempfile.mktemp(suffix=".mp4")
    r = subprocess.run([
        "ffmpeg", "-y", "-i", bg_video, "-i", audio, "-shortest",
        "-c:v", "copy", "-c:a", "copy", "-movflags", "+faststart", base_video
    ], capture_output=True, timeout=30)
    if r.returncode != 0 or not os.path.exists(base_video):
        print(f"   ⚠️ Mix failed, using bg video without audio: {r.stderr[:100]}")
        base_video = bg_video
    else:
        os.remove(bg_video)
    if os.path.exists(audio): os.remove(audio)
    print("   ✅ Mix done")
    
    # 4. Generate caption overlay
    print("4. Rendering captions...")
    cap_dir, fps = generate_caption_frames(w, h, duration, fps, text)
    cap_video = tempfile.mktemp(suffix="_cap.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", f"{cap_dir}/f_%05d.png",
        "-c:v", "png", "-pix_fmt", "rgba", cap_video
    ], capture_output=True, timeout=60)
    shutil.rmtree(cap_dir, ignore_errors=True)
    print("   ✅ Captions done")
    
    # 5. Composite
    print("5. Compositing (overlay + bounce)...")
    subprocess.run([
        "ffmpeg", "-y", "-i", base_video, "-i", cap_video,
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1[ov];[ov]format=yuv420p[out]",
        "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", output_path
    ], capture_output=True, timeout=120)
    os.remove(base_video)
    os.remove(cap_video)
    print("   ✅ Composite done")
    
    # Verify
    sz = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n✅ Done: {output_path}")
    print(f"   Size: {sz:.1f} MB")
    print(f"   Ready to upload to TikTok/Instagram Reels")
    return output_path


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "This is AutoEdit. AI-powered video editing."
    out = sys.argv[2] if len(sys.argv) > 2 else "tiktok_output.mp4"
    create_tiktok_video(text, out)
