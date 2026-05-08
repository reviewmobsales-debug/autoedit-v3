"""Whisper transcription with caching."""

import whisper, json, hashlib, time

def get_cached_transcript(video_path, exports_dir):
    with open(video_path, "rb") as fh:
        fh_hash = hashlib.md5(fh.read(1024*1024)).hexdigest()[:16]
    cache_file = exports_dir / f"cache_{fh_hash}.json"
    if cache_file.exists():
        try:
            with open(cache_file) as fj:
                data = json.load(fj)
                return data["segments"], data["text"]
        except: pass
    return None, None

def save_cached_transcript(video_path, segments, text, exports_dir):
    with open(video_path, "rb") as fh:
        fh_hash = hashlib.md5(fh.read(1024*1024)).hexdigest()[:16]
    cache_file = exports_dir / f"cache_{fh_hash}.json"
    with open(cache_file, "w") as fj:
        json.dump({"segments": segments, "text": text}, fj)

def transcribe_video(video_path, model_name="base"):
    """Transcribe video using Whisper with MPS GPU acceleration."""
    import whisper, torch, os
    
    cache_dir = BASE / "whisper_cache"
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / (Path(video_path).stem + ".json")
    
    if cache_file.exists():
        import json
        with open(cache_file) as f:
            return json.load(f)
    
    audio_path = str(Path(video_path).with_suffix(".wav"))
    if not os.path.exists(audio_path):
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1", audio_path
        ], capture_output=True, timeout=60)
    
    # EXPLICIT MPS DEVICE
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"   [Whisper] Loading model on {device.upper()}")
    
    model = whisper.load_model(model_name, device=device)
    
    result = model.transcribe(audio_path, word_timestamps=True, fp16=False)
    
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip()
        })
    
    if cache_file:
        import json
        with open(cache_file, "w") as f:
            json.dump(segments, f)
    
    return segments
