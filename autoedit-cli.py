#!/usr/bin/env python3
"""AutoEdit CLI — Batch process videos from command line.
Usage: python3 autoedit-cli.py input.mp4 --style tiktok --output out.mp4"""
import argparse, requests, time, os, sys

def main():
    parser = argparse.ArgumentParser(description="AutoEdit CLI")
    parser.add_argument("input", help="Input video path")
    parser.add_argument("--style", default="tiktok", choices=["tiktok","youtube","neon","cinematic","clean"])
    parser.add_argument("--silence", action="store_true", help="Remove silences")
    parser.add_argument("--server", default="http://127.0.0.1:5002", help="Server URL")
    parser.add_argument("--output", default="", help="Output filename")
    args = parser.parse_args()

    server = args.server.rstrip("/")
    print(f"AutoEdit CLI: {args.input} → style={args.style}")
    
    # Upload
    print("Uploading...", end=" ", flush=True)
    r = requests.post(f"{server}/api/upload", files={"file": open(args.input, "rb")}, timeout=30)
    assert r.json().get("ok"), f"Upload failed: {r.json()}")
    path = r.json()["uploaded"]
    print("OK")
    
    # Edit
    print("Rendering...", end=" ", flush=True)
    r = requests.post(f"{server}/api/edit", json={
        "path": path, "removeSilences": args.silence,
        "autoCaptions": True, "captionStyle": args.style
    }, timeout=300)
    data = r.json()
    assert data.get("ok"), f"Edit failed: {data.get('error')}"
    print("OK")
    
    # Download
    out = args.output or f"autoedit_{args.style}_{os.path.basename(args.input)}"
    r = requests.get(f"{server}/api/download?path={data['output']}", timeout=60)
    with open(out, "wb") as f:
        f.write(r.content)
    
    saved = data.get("originalDuration",0) - data.get("finalDuration",0)
    print(f"\n✅ Done: {out}")
    print(f"   Original: {data.get('originalDuration','?'):.1f}s")
    print(f"   Final: {data.get('finalDuration','?'):.1f}s")
    if saved > 0:
        print(f"   Saved: {saved:.1f}s")

if __name__ == "__main__":
    main()
