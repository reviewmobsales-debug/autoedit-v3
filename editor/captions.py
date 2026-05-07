"""Caption rendering with PIL — 5 styles: tiktok, youtube, neon, cinematic, clean."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

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
    
    # Pink glow
    glow = Image.new("RGBA", (w,h), (0,0,0,0))
    g = ImageDraw.Draw(glow)
    for r in range(20,4,-4):
        a = int(40 * r/20)
        g.text((x,y), text, font=font, fill=(255,50,150,a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=6))
    img.paste(Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB"), (0,0))
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Pill
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
