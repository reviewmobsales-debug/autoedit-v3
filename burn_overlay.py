"""
AutoEdit Burn Engine — PIL text frames + ffmpeg overlay (NO drawtext needed)
Works with ANY ffmpeg build, even without freetype.
"""
import subprocess, os, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def burn_text_overlay(video_path, output_path, text_lines, style="tiktok"):
    """
    Burn text captions using PIL-generated PNG frames + ffmpeg overlay.
    No drawtext filter needed.
    """
    # Get video info
    probe = subprocess.run(
        ["ffprobe","-v","error","-select_streams","v:0",
         "-show_entries","stream=width,height,r_frame_rate,duration",
         "-of","csv"], 
        capture_output=True, text=True, timeout=10
    )
    # Parse: width,height,frame_rate,duration
    parts = probe.stdout.strip().split('\n')[0].split(',')
    w, h = int(parts[0]), int(parts[1])
    fps_num, fps_den = map(int, parts[2].split('/'))
    fps = fps_num / fps_den if fps_den else 30
    duration = float(parts[3]) if len(parts) > 3 else 0
    
    # Generate overlay frames
    frames_dir = tempfile.mkdtemp(prefix="overlay_")
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    font_large = ImageFont.truetype(font_path, min(h // 14, 80))
    
    total_frames = int(duration * fps) if duration else 30
    
    for frame_idx in range(total_frames):
        # Create transparent overlay
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Show one line at a time, cycling through
        line_idx = min(frame_idx // max(total_frames // len(text_lines), 1), len(text_lines) - 1)
        text = text_lines[line_idx]
        
        if style == "tiktok":
            y = int(h * 0.75)
            bbox = draw.textbbox((0, 0), text, font=font_large)
            tw_text = bbox[2] - bbox[0]
            th_text = bbox[3] - bbox[1]
            x = (w - tw_text) // 2
            
            # Glow
            for dx, dy in [(i, j) for i in range(-8, 9, 2) for j in range(-8, 9, 2)]:
                draw.text((x + dx, y + dy), text, font=font_large, fill=(255, 50, 150, 40))
            
            # Pill
            draw.rounded_rectangle(
                [x - 30, y - 16, x + tw_text + 30, y + th_text + 16],
                radius=20, fill=(0, 0, 0, 160)
            )
            
            # Outline
            for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
                draw.text((x + dx, y + dy), text, font=font_large, fill=(0, 0, 0, 200))
            
            # White text
            draw.text((x, y), text, font=font_large, fill=(255, 255, 255))
        
        # Save frame
        overlay.save(f"{frames_dir}/frame_{frame_idx:05d}.png")
    
    # Burn overlay onto video using ffmpeg overlay filter (not drawtext!)
    # Create a video from the overlay frames
    overlay_video = f"{frames_dir}/overlay.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", f"{frames_dir}/frame_%05d.png",
        "-c:v", "png", "-pix_fmt", "rgba",
        overlay_video
    ], capture_output=True, timeout=60)
    
    # Overlay with alpha compositing
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", overlay_video,
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1[ov];[ov]format=yuv420p[out]",
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output_path)
    ], capture_output=True, timeout=120)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    return os.path.exists(output_path)


if __name__ == "__main__":
    import sys
    video = sys.argv[1] if len(sys.argv) > 1 else "/tmp/silence_test.mp4"
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/overlay_test.mp4"
    
    ok = burn_text_overlay(video, out, ["HELLO WORLD", "THIS IS AUTOEDIT", "TikTok Style!"], "tiktok")
    print(f"{'✅' if ok else '❌'} Result: {out}")
