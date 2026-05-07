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

def transcribe_video(video_path, model="base"):
    """Real Whisper transcription with word-level timing."""
    import whisper
    
    wmodel = whisper.load_model(model)
    result = wmodel.transcribe(str(video_path), word_timestamps=True)
    
    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "words": seg.get("words", [])
        })
    return segments, result["text"]



