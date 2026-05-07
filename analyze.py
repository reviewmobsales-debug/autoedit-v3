#!/usr/bin/env python3
"""AutoEdit Orientation Analyzer — Detect video format and suggest optimal settings."""
import subprocess, sys
from pathlib import Path

def analyze_video(video_path):
    """Detect orientation, duration, and suggest TikTok/YouTube/Instagram format."""
    # Get dimensions
    r = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json", video_path
    ], capture_output=True, text=True, timeout=10)
    
    data = json.loads(r.stdout)
    stream = data.get("streams", [{}])[0]
    w = stream.get("width", 1920)
    h = stream.get("height", 1080)
    dur = float(stream.get("duration", 0))
    
    aspect = w / h
    
    # Determine orientation and recommendation
    if aspect < 0.8:
        orientation = "VERTICAL (9:16 or similar)"
        recommendation = {
            "best_for": ["TikTok", "Instagram Reels", "YouTube Shorts"],
            "suggested_style": "tiktok",
            "needs_crop": False,
            "note": "Already optimized for vertical platforms"
        }
    elif aspect > 1.5:
        orientation = "HORIZONTAL (16:9 or wider)"
        recommendation = {
            "best_for": ["YouTube", "Landscape video"],
            "suggested_style": "youtube",
            "needs_crop": True,
            "crop_to": "9:16 (center crop for TikTok)",
            "note": "Consider cropping to vertical for TikTok/Reels"
        }
    else:
        orientation = "SQUARE (1:1 or close)"
        recommendation = {
            "best_for": ["Instagram", "Facebook"],
            "suggested_style": "clean",
            "needs_crop": False,
            "note": "Works everywhere but not optimal for TikTok"
        }
    
    result = {
        "file": video_path,
        "width": w,
        "height": h,
        "aspect_ratio": round(aspect, 2),
        "duration_seconds": round(dur, 1),
        "orientation": orientation,
        "recommendation": recommendation
    }
    
    return result

def print_analysis(result):
    print(f"\n{'='*60}")
    print(f"📹 Video Analysis: {Path(result['file']).name}")
    print(f"{'='*60}")
    print(f"Resolution: {result['width']}x{result['height']}")
    print(f"Aspect: {result['aspect_ratio']}")
    print(f"Duration: {result['duration_seconds']}s")
    print(f"Orientation: {result['orientation']}")
    print(f"\n💡 Recommendation:")
    rec = result['recommendation']
    print(f"   Best for: {', '.join(rec['best_for'])}")
    print(f"   Suggested style: {rec['suggested_style']}")
    print(f"   Needs crop: {rec['needs_crop']}")
    if rec.get('crop_to'):
        print(f"   Crop to: {rec['crop_to']}")
    print(f"   Note: {rec['note']}")
    print(f"{'='*60}")

if __name__ == "__main__":
    import json
    video = sys.argv[1] if len(sys.argv) > 1 else "/tmp/silence_test.mp4"
    result = analyze_video(video)
    print_analysis(result)
    
    # Save JSON
    out = Path(video).with_suffix('.analysis.json')
    with open(out, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"📄 Saved: {out}")
