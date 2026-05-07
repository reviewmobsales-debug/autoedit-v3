"""Video effects: silence removal, face crop, speed ramp."""
import subprocess, tempfile, shutil, os, re

def get_duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True, timeout=10)
    try: return float(r.stdout.strip())
    except: return 0.0

def remove_silences(input_path, output_path, threshold="-40dB", min_duration=0.3):
    """Detect silent parts and splice video using concat demuxer."""
    detect = subprocess.run([
        "ffmpeg","-y","-i",str(input_path),"-af",
        f"silencedetect=noise={threshold}:d={min_duration}","-f","null","-"
    ], capture_output=True, text=True, timeout=30)
    
    starts = re.findall(r'silence_start:\s*([\d\.]+)', detect.stderr)
    ends = re.findall(r'silence_end:\s*([\d\.]+)', detect.stderr)
    silence = [(float(s),float(e)) for s,e in zip(starts, ends)]
    
    if not silence:
        subprocess.run(["ffmpeg","-y","-i",str(input_path),"-c","copy",str(output_path)], capture_output=True, timeout=30)
        return True
    
    total = get_duration(input_path)
    segments = []
    cursor = 0.0
    for s_start, s_end in silence:
        if s_start - cursor >= 0.1:
            segments.append((cursor, s_start))
        cursor = s_end
    if total - cursor >= 0.1:
        segments.append((cursor, total))
    
    tmpdir = tempfile.mkdtemp(prefix="silentrm_")
    clips = []
    for i, (seg_start, seg_end) in enumerate(segments):
        clip = f"{tmpdir}/clip_{i:04d}.mp4"
        r = subprocess.run(["ffmpeg","-y","-i",str(input_path),"-ss",str(seg_start),
            "-t",str(seg_end - seg_start),"-c","copy","-avoid_negative_ts","make_zero", clip],
            capture_output=True, timeout=60)
        if r.returncode == 0 and os.path.exists(clip) and os.path.getsize(clip) > 1000:
            clips.append(clip)
    
    if not clips:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False
    
    listfile = f"{tmpdir}/list.txt"
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    
    r = subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",listfile,
        "-c","copy","-movflags","+faststart", str(output_path)], capture_output=True, timeout=120)
    
    shutil.rmtree(tmpdir, ignore_errors=True)
    return r.returncode == 0 and os.path.exists(output_path)
