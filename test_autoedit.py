#!/usr/bin/env python3
"""AutoEdit v3 Test Suite — Run with: python3 test_autoedit.py"""
import requests, subprocess, os, json, time

SERVER = "http://127.0.0.1:5002"

def test_health():
    r = requests.get(f"{SERVER}/api/health", timeout=5)
    assert r.status_code == 200 and r.json().get("ok"), "Health failed"
    print("✅ test_health")

def test_upload_and_edit():
    """Full pipeline test with all styles."""
    styles = ["tiktok", "youtube", "neon", "cinematic", "clean"]
    
    for style in styles:
        # Generate tiny test video
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i",
            "testsrc=duration=2:size=1080x1920:rate=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "/tmp/test_style.mp4"
        ], capture_output=True, timeout=15)
        
        # Upload
        r = requests.post(f"{SERVER}/api/upload",
                          files={"file": open("/tmp/test_style.mp4", "rb")},
                          timeout=30)
        assert r.status_code == 200, f"Upload failed for {style}"
        up = r.json()
        assert up.get("ok"), f"Upload error for {style}"
        
        # Edit
        r2 = requests.post(f"{SERVER}/api/edit", json={
            "path": up["uploaded"],
            "removeSilences": False,
            "autoCaptions": True,
            "captionStyle": style
        }, timeout=120)
        assert r2.status_code == 200, f"Edit HTTP fail for {style}"
        edit = r2.json()
        assert edit.get("ok"), f"Edit failed for {style}: {edit.get('error')}"
        
        # Verify file exists
        assert os.path.exists(edit["output"]), f"Output missing for {style}"
        
        # Verify duration
        dur = float(subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", edit["output"]
        ], capture_output=True, text=True, timeout=5).stdout.strip())
        assert dur > 0, f"Invalid duration for {style}"
        
        print(f"✅ test_{style}: {dur:.1f}s")
        time.sleep(0.5)

if __name__ == "__main__":
    print("="*60)
    print("AutoEdit v3 Test Suite")
    print("="*60)
    try:
        test_health()
        test_upload_and_edit()
        print(f"{'='*60}")
        print("ALL TESTS PASSED ✅")
        print(f"{'='*60}")
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
