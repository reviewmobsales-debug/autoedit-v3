"""Caption rendering with PIL — 5 styles: tiktok, youtube, neon, cinematic, clean."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import subprocess, os, tempfile, shutil

def render_caption_style(draw, img, w, h, active_text, style):
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    font_large = ImageFont.truetype(font_path, min(h // 14, 80))
    font_medium = ImageFont.truetype(font_path, min(h // 18, 56))
    font_small = ImageFont.truetype(font_path, min(h // 22, 40))
    
    if style == "tiktok":
        _render_tiktok(draw, img, w, h, active_text, font_large)
    elif style == "youtube":
        _render_youtube(draw, img, w, h, active_text, font_medium)
    elif style == "neon":
        _render_neon(draw, img, w, h, active_text, font_large)
    elif style == "cinematic":
        _render_cinematic(draw, img, w, h, active_text, font_medium)
    else:
        _render_clean(draw, img, w, h, active_text, font_medium)

def _render_tiktok(draw, img, w, h, text, font):
    y = int(h * 0.76)
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (w - tw) // 2
    
    glow = Image.new("RGBA", (w,h), (0,0,0,0))
    g = ImageDraw.Draw(glow)
    for r in range(20,4,-4):
        a = int(40 * r/20)
        g.text((x,y), text, font=font, fill=(255,50,150,a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=6))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0,0))
    draw = ImageDraw.Draw(img, "RGBA")
    
    draw.rounded_rectangle([x-36,y-20,x+tw+36,y+th+20], radius=24, fill=(0,0,0,160))
    for dx,dy in [(-6,0),(6,0),(0,-6),(0,6)]:
        draw.text((x+dx,y+dy), text, font=font, fill=(0,0,0,220))
    draw.text((x,y), text, font=font, fill=(255,255,255))

def _render_youtube(draw, img, w, h, text, font):
    y = int(h * 0.89)
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    x = (w - tw) // 2
    draw.rectangle([0,y-14,w,y+40+18], fill=(0,0,0,140))
    draw.text((x,y), text, font=font, fill=(255,255,255))

def _render_neon(draw, img, w, h, text, font):
    y = int(h * 0.72)
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (w - tw) // 2
    
    glow = Image.new("RGBA", (w,h), (0,0,0,0))
    g = ImageDraw.Draw(glow)
    for r in range(15,2,-3):
        a = int(50*r/15)
        g.text((x,y), text, font=font, fill=(0,255,255,a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=4))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0,0))
    draw = ImageDraw.Draw(img, "RGBA")
    
    draw.rounded_rectangle([x-30,y-16,x+tw+30,y+th+16], radius=18, fill=(20,0,40,200))
    for dx,dy in [(-3,0),(3,0)]:
        draw.text((x+dx,y+dy), text, font=font, fill=(0,200,255,150))
    draw.text((x,y), text, font=font, fill=(0,255,255))

def _render_cinematic(draw, img, w, h, text, font):
    bar = int(h * 0.08)
    draw.rectangle([0,0,w,bar], fill=(0,0,0))
    draw.rectangle([0,h-bar,w,h], fill=(0,0,0))
    y = int(h * 0.78)
    t = text.upper()
    bbox = draw.textbbox((0,0), t, font=font)
    tw = bbox[2]-bbox[0]
    x = (w - tw) // 2
    for dx,dy in [(-2,0),(2,0)]:
        draw.text((x+dx,y+dy), t, font=font, fill=(0,0,0,180))
    draw.text((x,y), t, font=font, fill=(255,230,150))

def _render_clean(draw, img, w, h, text, font):
    y = int(h * 0.84)
    bbox = draw.textbbox((0,0), text, font=font)
    tw = bbox[2]-bbox[0]
    x = (w - tw) // 2
    for dx,dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
        draw.text((x+dx,y+dy), text, font=font, fill=(0,0,0,120))
    draw.text((x,y), text, font=font, fill=(255,255,255))

def burn_captions_from_whisper(input_path, output_path, segments, style="tiktok"):
    """Burn captions using PIL (frame-by-frame extraction + reconstruction)."""
    frames_dir = tempfile.mkdtemp(prefix="frames_")
    subprocess.run([
        "ffmpeg","-y","-i",str(input_path),
        "-vf","fps=30,scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-pix_fmt","rgb24", f"{frames_dir}/frame_%05d.png"
    ], capture_output=True, timeout=120)
    
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.png')])
    if not frames:
        subprocess.run(["ffmpeg","-y","-i",str(input_path),"-c","copy",str(output_path)], capture_output=True, timeout=30)
        return False
    
    fps = 30.0
    frame_dur = 1.0 / fps
    
    for idx, frame_file in enumerate(frames):
        frame_time = idx * frame_dur + (frame_dur / 2)
        img = Image.open(f"{frames_dir}/{frame_file}")
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.size
        
        active_text = ""
        for seg in segments:
            if seg.get("start",0) <= frame_time <= seg.get("end",0):
                active_text = seg.get("text","")
                break
        
        if active_text:
            render_caption_style(draw, img, w, h, active_text, style)
        
        draw.text((w-140, 20), "AutoEdit", font=ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30), fill=(255,255,255,180))
        img.save(f"{frames_dir}/{frame_file}")
    
    subprocess.run([
        "ffmpeg","-y","-framerate","30","-i",f"{frames_dir}/frame_%05d.png",
        "-i",str(input_path),"-map","0:v","-map","1:a",
        "-c:v","libx264","-preset","fast","-crf","23",
        "-c:a","copy","-pix_fmt","yuv420p","-shortest", str(output_path)
    ], capture_output=True, timeout=120)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    return os.path.exists(output_path)

def burn_captions_overlay(input_path, output_path, segments, style="tiktok"):
    """Burn captions using PIL + ffmpeg overlay. No drawtext filter needed."""
    probe = subprocess.run([
        "ffprobe","-v","error","-select_streams","v:0",
        "-show_entries","stream=width,height,r_frame_rate,duration",
        "-of","csv=p=0:s=x"
    ], capture_output=True, text=True, timeout=10)
    line = probe.stdout.strip().split(chr(10))[0]
    parts = [p for p in line.split('x') if p]
    if len(parts) >= 4:
        w, h = int(parts[0]), int(parts[1])
        fps_s = parts[2]
        dur = float(parts[3])
    else:
        w, h, fps_s, dur = 1080, 1920, "30", 8.0
    
    if '/' in fps_s:
        num, den = map(int, fps_s.split('/'))
        fps = num / den if den else 30
    else:
        fps = float(fps_s) if fps_s else 30
    
    total_frames = int(dur * fps)
    lines = [s.get("text","") for s in segments[:4]] if segments else ["Caption"]
    
    frames_dir = tempfile.mkdtemp(prefix="capov_")
    fpath = "/System/Library/Fonts/Helvetica.ttc"
    fl = ImageFont.truetype(fpath, min(h // 14, 72))
    
    per_line = max(total_frames // len(lines), 1)
    
    for i in range(total_frames):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        li = min(i // per_line, len(lines) - 1)
        txt = lines[li]
        
        y = int(h * 0.75)
        bb = draw.textbbox((0, 0), txt, font=fl)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        x = (w - tw) // 2
        
        for dx, dy in [(i, j) for i in range(-6, 9, 3) for j in range(-6, 9, 3)]:
            draw.text((x + dx, y + dy), txt, font=fl, fill=(255, 50, 150, 25))
        
        draw.rounded_rectangle([x - 24, y - 14, x + tw + 24, y + th + 14], radius=18, fill=(0, 0, 0, 150))
        
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            draw.text((x + dx, y + dy), txt, font=fl, fill=(0, 0, 0, 200))
        
        draw.text((x, y), txt, font=fl, fill=(255, 255, 255))
        
        img.save(f"{frames_dir}/f{i:05d}.png")
    
    ov = f"{frames_dir}/ov.mp4"
    subprocess.run(["ffmpeg", "-y", "-framerate", str(fps),
                   "-i", f"{frames_dir}/f_%05d.png",
                   "-c:v", "png", "-pix_fmt", "rgba", ov],
                  capture_output=True, timeout=60)
    
    subprocess.run(["ffmpeg", "-y", "-i", str(input_path), "-i", ov,
        "-filter_complex", "[0:v][1:v]overlay=0:0:shortest=1[ov];[ov]format=yuv420p[out]",
        "-map", "[out]", "-map", "0:a", "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output_path)],
        capture_output=True, timeout=120)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    return os.path.exists(output_path)
