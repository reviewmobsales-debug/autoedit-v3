"""
AutoEdit v3 — The Simple, Working Version
5 files total. No complexity. Just works.

Architecture:
- main.py      → Flask API + minimal UI
- engine.py    → auto-edit logic (silence + captions)
- fonts.py     → download/cache fonts
- web/         → single HTML file
- uploads/     → temp storage
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
import subprocess
import os
import tempfile
import time
from pathlib import Path
from face_crop import auto_crop_vertical

app = Flask(__name__, static_folder=None)
BASE = Path(__file__).parent.resolve()
UPLOADS = BASE / "uploads"
EXPORTS = BASE / "exports"
UPLOADS.mkdir(exist_ok=True)
EXPORTS.mkdir(exist_ok=True)

# ════════════════════════════════════════════════════════════════
#  SIMPLE API
# ════════════════════════════════════════════════════════════════

def _ok(data): return jsonify({"ok": True, **data})
def _err(msg, code=400): return jsonify({"ok": False, "error": msg}), code

@app.route("/api/health")
def health(): return _ok({"status": "ready"})

@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>AutoEdit v3</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
body{background:#0a0a0f;color:#fff;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:20px}
header{width:100%;max-width:500px;text-align:center;background:linear-gradient(135deg,#667eea,#764ba2);padding:24px;border-radius:16px;margin-bottom:24px}
h1{font-size:32px;font-weight:800;letter-spacing:-1px}
p.sub{opacity:.8;font-size:14px;margin-top:4px}
.drop{width:100%;max-width:500px;height:200px;border:3px dashed rgba(255,255,255,.2);border-radius:20px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;cursor:pointer;transition:.3s}
.drop:hover{border-color:#667eea;background:rgba(102,126,234,.05)}
.drop .icon{font-size:48px}
.drop p{font-size:18px}
.drop .hint{opacity:.5;font-size:13px}
input[type="file"]{display:none}
.settings{width:100%;max-width:500px;background:rgba(255,255,255,.05);border-radius:16px;padding:20px;margin-top:20px;display:none}
.settings.show{display:block}
.settings h2{font-size:18px;margin-bottom:16px}
.row{display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid rgba(255,255,255,.08)}
.row:last-child{border:none}
.row span{font-size:15px}
.toggle{width:48px;height:28px;background:rgba(255,255,255,.15);border-radius:14px;position:relative;cursor:pointer;transition:.3s}
.toggle.on{background:#667eea}
.toggle::after{content:'';position:absolute;width:22px;height:22px;background:#fff;border-radius:50%;top:3px;left:3px;transition:.3s}
.toggle.on::after{left:23px}
.styles{display:flex;gap:8px;margin-top:12px}
.style-btn{flex:1;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,.15);background:none;color:#fff;font-size:13px;cursor:pointer}
.style-btn.active{background:rgba(102,126,234,.2);border-color:#667eea}
.btn{width:100%;max-width:500px;padding:16px;border-radius:12px;border:none;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;font-size:18px;font-weight:600;cursor:pointer;margin-top:20px;opacity:.4;pointer-events:none}
.btn.ready{opacity:1;pointer-events:auto}
.progress{width:100%;max-width:500px;text-align:center;padding:30px 20px;display:none}
.bar{height:8px;background:rgba(255,255,255,.1);border-radius:4px;overflow:hidden;margin-bottom:12px}
.fill{height:100%;width:0%;background:linear-gradient(90deg,#667eea,#764ba2);border-radius:4px;transition:.4s}
.result{width:100%;max-width:500px;text-align:center;display:none}
.result video{width:100%;border-radius:12px;background:#000}
.result a{display:inline-block;padding:14px 32px;border-radius:12px;background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;text-decoration:none;font-weight:600;margin-top:12px}
#fileName{margin-top:12px;font-size:14px;opacity:.6}
</style>
</head>
<body>
<header><h1>AutoEdit v3</h1><p class="sub">Drag, drop, done.</p></header>

<div class="drop" id="dropZone">
  <div class="icon">📹</div>
  <p>Drop your video here</p>
  <p class="hint">or click to browse</p>
  <input type="file" id="fileInput" accept="video/*">
</div>
<p id="fileName"></p>

<div class="settings" id="settings">
  <h2>⚙️ AI Features</h2>
  <div class="row"><span>Remove Silences</span><div class="toggle on" data-opt="removeSilences"></div></div>
  <div class="row"><span>Auto Captions</span><div class="toggle on" data-opt="captions"></div></div>
  <div class="row"><span style="font-size:13px;opacity:.6">Caption Style</span></div>
  <div class="styles">
    <button class="style-btn active" data-style="tiktok">TikTok</button>
    <button class="style-btn" data-style="youtube">YouTube</button>
    <button class="style-btn" data-style="clean">Clean</button>
  </div>
</div>

<button class="btn" id="btnEdit">🚀 Auto Edit</button>

<div class="progress" id="progress">
  <div class="bar"><div class="fill" id="fill"></div></div>
  <p id="progText">Starting...</p>
</div>

<div class="result" id="result">
  <h2 style="margin-bottom:16px">✅ Done!</h2>
  <video id="resultVid" controls playsinline></video>
  <br><a id="dlLink" download>⬇️ Download</a>
</div>

<script>
let file=null, style='tiktok';
const drop=document.getElementById('dropZone'), input=document.getElementById('fileInput');
drop.onclick=()=>input.click();
drop.addEventListener('dragover',e=>{e.preventDefault();drop.style.borderColor='#667eea'});
drop.addEventListener('dragleave',()=>drop.style.borderColor='rgba(255,255,255,.2)');
drop.addEventListener('drop',e=>{e.preventDefault();drop.style.borderColor='rgba(255,255,255,.2)';handleFile(e.dataTransfer.files[0])});
input.onchange=e=>handleFile(e.target.files[0]);

function handleFile(f){
  if(!f||!f.type.startsWith('video/'))return alert('Need video');
  file=f;
  document.getElementById('fileName').textContent=f.name+' — '+(f.size>1024**2?(f.size/1024**2).toFixed(1)+' MB':(f.size/1024).toFixed(0)+' KB');
  drop.innerHTML='<p style="font-size:24px">✅</p><p>'+f.name+'</p>';
  drop.style.borderStyle='solid';
  document.getElementById('settings').classList.add('show');
  document.getElementById('btnEdit').classList.add('ready');
}

document.querySelectorAll('.toggle').forEach(t=>t.onclick=function(){this.classList.toggle('on')});
document.querySelectorAll('.style-btn').forEach(b=>b.onclick=function(){
  document.querySelectorAll('.style-btn').forEach(x=>x.classList.remove('active'));
  this.classList.add('active');style=this.dataset.style;
});

document.getElementById('btnEdit').onclick=async()=>{
  if(!file)return;
  const btn=document.getElementById('btnEdit');btn.disabled=true;btn.textContent='🔄 Editing...';
  document.getElementById('progress').style.display='block';
  document.getElementById('fill').style.width='10%';
  try{
    const fd=new FormData();fd.append('file',file);
    const upl=await(await fetch('/api/upload',{method:'POST',body:fd})).json();
    if(!upl.ok)throw new Error(upl.error);
    document.getElementById('fill').style.width='40%';
    document.getElementById('progText').textContent='AI editing...';
    const opts=document.querySelectorAll('.toggle');
    const edit=await(await fetch('/api/edit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
      path:upl.uploaded,
      removeSilences:opts[0].classList.contains('on'),
      autoCaptions:opts[1].classList.contains('on'),
      captionStyle:style
    })})).json();
    if(!edit.ok)throw new Error(edit.error);
    document.getElementById('fill').style.width='100%';
    document.getElementById('progText').textContent='Done!';
    const outPath=edit.output;
    document.getElementById('result').style.display='block';
    const url='/api/download?path='+encodeURIComponent(outPath);
    document.getElementById('resultVid').src=url;
    document.getElementById('dlLink').href=url;
    document.getElementById('result').scrollIntoView({behavior:'smooth'});
  }catch(e){
    document.getElementById('progText').textContent='Error: '+e.message;
    document.getElementById('progText').style.color='#ff6b6b';
    btn.disabled=false;btn.textContent='🚀 Retry';
  }
};
</script>
</body>
</html>
    """

# ════════════════════════════════════════════════════════════════
#  FILE UPLOAD
# ════════════════════════════════════════════════════════════════

@app.route("/api/upload", methods=["POST"])
def upload():
    vid = request.files.get("file")
    if not vid or vid.filename == "":
        return _err("no file")
    dest = UPLOADS / ("upload_" + str(int(time.time())) + "_" + vid.filename)
    vid.save(str(dest))
    return _ok({"uploaded": str(dest), "filename": dest.name})

# ════════════════════════════════════════════════════════════════
#  EDIT ENGINE
# ════════════════════════════════════════════════════════════════


# ════════════════════════════════════════════════════════════════
#  RETRY WRAPPER
# ════════════════════════════════════════════════════════════════

def retry_ffmpeg(cmd, max_retries=2, timeout=120):
    """Run ffmpeg command with auto-retry on failure."""
    for attempt in range(max_retries):
        r = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if r.returncode == 0:
            return True
        err = r.stderr.decode('utf-8', errors='ignore') if r.stderr else ""
        if "Cannot allocate memory" in err or "Resource temporarily unavailable" in err:
            print(f"ffmpeg attempt {attempt+1}/{max_retries} failed, retrying...")
            time.sleep(0.5 * (attempt + 1))
        else:
            # Real error, log and fail
            print(f"ffmpeg failed: {err[:200]}")
            return False
    return False

def get_duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True, timeout=10)
    try: return float(r.stdout.strip())
    except: return 0.0

def remove_silences(input_path, output_path, threshold="-40dB", min_duration=0.3):
    """Remove silent/dead-air segments using ffmpeg concat demuxer."""
    import re, tempfile, json
    
    # Step 1: Detect silence periods
    detect = subprocess.run([
        "ffmpeg","-y","-i",str(input_path),"-af",
        f"silencedetect=noise={threshold}:d={min_duration}",
        "-f","null","-"
    ], capture_output=True, text=True, timeout=30)
    
    starts = re.findall(r'silence_start:\s*([\d\.]+)', detect.stderr)
    ends   = re.findall(r'silence_end:\s*([\d\.]+)',   detect.stderr)
    silence = [(float(s), float(e)) for s, e in zip(starts, ends)]
    
    if not silence:
        subprocess.run(["ffmpeg","-y","-i",str(input_path),"-c","copy",str(output_path)],
                     capture_output=True, timeout=30)
        return True
    
    # Step 2: Build non-silent segments
    total = get_duration(input_path)
    segments = []
    cursor = 0.0
    for s_start, s_end in silence:
        if s_start - cursor >= 0.1:
            segments.append((cursor, s_start))
        cursor = s_end
    if total - cursor >= 0.1:
        segments.append((cursor, total))
    
    # Step 3: Extract clips and concat
    tmpdir = tempfile.mkdtemp(prefix="silentrm_")
    clips = []
    for i, (seg_start, seg_end) in enumerate(segments):
        clip = f"{tmpdir}/clip_{i:04d}.mp4"
        r = subprocess.run([
            "ffmpeg","-y","-i",str(input_path),"-ss",str(seg_start),
            "-t",str(seg_end - seg_start),"-c","copy","-avoid_negative_ts","make_zero",
            clip
        ], capture_output=True, timeout=60)
        if r.returncode == 0 and os.path.exists(clip) and os.path.getsize(clip) > 1000:
            clips.append(clip)
    
    if not clips:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return False
    
    # Step 4: Concat
    listfile = f"{tmpdir}/list.txt"
    with open(listfile, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    
    r = subprocess.run([
        "ffmpeg","-y","-f","concat","-safe","0","-i",listfile,
        "-c","copy","-movflags","+faststart", str(output_path)
    ], capture_output=True, timeout=120)
    
    shutil.rmtree(tmpdir, ignore_errors=True)
    return r.returncode == 0 and os.path.exists(output_path)


# ════════════════════════════════════════════════════════════════
#  PROGRESS TRACKING
# ════════════════════════════════════════════════════════════════

PROGRESS_FILE = BASE / "progress.json"

def get_progress(job_id):
    """Get current job progress from file."""
    if PROGRESS_FILE.exists():
        try:
            import json
            with open(PROGRESS_FILE) as f:
                data = json.load(f)
                return data.get(job_id, {})
        except:
            pass
    return {}

def set_progress(job_id, phase, percent, detail=""):
    """Update job progress in file."""
    import json
    data = {}
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE) as f:
                data = json.load(f)
        except:
            pass
    data[job_id] = {
        "phase": phase,
        "percent": percent,
        "detail": detail,
        "timestamp": time.time()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f)

@app.route("/api/progress/<job_id>")
def get_progress_route(job_id):
    """Pollable progress endpoint."""
    prog = get_progress(job_id)
    if prog:
        return _ok(prog)
    return _err("job not found")


@app.route("/api/crop-to-vertical", methods=["POST"])
def crop_vertical():
    """Auto-crop video to vertical TikTok format (9:16) with face detection."""
    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path or not os.path.exists(path):
        return _err("file not found")
    
    out = EXPORTS / ("vertical_" + str(int(time.time())) + ".mp4")
    ok = auto_crop_vertical(path, out)
    
    if ok and out.exists():
        dur = get_duration(out)
        return _ok({
            "output": str(out),
            "duration": round(dur, 2),
            "message": "Auto-cropped to vertical 9:16 with face detection"
        })
    return _err("face crop failed")


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


def burn_captions_from_whisper(input_path, output_path, segments, style="tiktok"):
    """Burn real Whisper captions with TikTok-style glow effects using PIL."""
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    
    # Extract frames
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
    
    # Font settings per style
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    font_large = ImageFont.truetype(font_path, 80)
    font_medium = ImageFont.truetype(font_path, 56)
    font_small = ImageFont.truetype(font_path, 40)
    
    text_lines = [seg["text"] for seg in segments[:4]]
    if not text_lines:
        text_lines = ["AutoEdit", "AI Captions", "Ready!"]
    
    for idx, frame_file in enumerate(frames):
        frame_time = idx * frame_dur + (frame_dur / 2)
        img = Image.open(f"{frames_dir}/{frame_file}")
        draw = ImageDraw.Draw(img, "RGBA")
        w, h = img.size
        
        # Find active text at this timestamp
        active_text = ""
        for seg in segments:
            if seg["start"] <= frame_time <= seg["end"]:
                active_text = seg["text"]
                break
        
        if active_text:
            if style == "tiktok":
                # TikTok: Large centered text with glow + rounded box
                y_pos = int(h * 0.75)
                font = font_large
                
                # Measure text
                bbox = draw.textbbox((0, 0), active_text, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                x_pos = (w - tw) // 2
                
                # Glow effect (multiple blurred outlines)
                glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                gdraw = ImageDraw.Draw(glow)
                for dx, dy in [(i, j) for i in range(-6, 7, 2) for j in range(-6, 7, 2)]:
                    gdraw.text((x_pos + dx, y_pos + dy), active_text, font=font, fill=(255, 50, 150, 30))
                glow = glow.filter(ImageFilter.GaussianBlur(radius=4))
                img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
                draw = ImageDraw.Draw(img, "RGBA")
                
                # Background capsule
                padding_x = 30
                padding_y = 16
                draw.rounded_rectangle(
                    [x_pos - padding_x, y_pos - padding_y, x_pos + tw + padding_x, y_pos + th + padding_y],
                    radius=20, fill=(0, 0, 0, 150)
                )
                
                # Bold outline
                for dx, dy in [(-4,-4),(-4,4),(4,-4),(4,4),(0,-4),(0,4),(-4,0),(4,0)]:
                    draw.text((x_pos + dx, y_pos + dy), active_text, font=font, fill=(0, 0, 0, 200))
                
                # White text
                draw.text((x_pos, y_pos), active_text, font=font, fill=(255, 255, 255))
                
            elif style == "youtube":
                # YouTube: Bottom-left aligned, smaller, box
                y_pos = int(h * 0.88)
                font = font_medium
                bbox = draw.textbbox((0, 0), active_text, font=font)
                tw = bbox[2] - bbox[0]
                x_pos = max(30, (w - tw) // 2)
                
                draw.rectangle([x_pos - 16, y_pos - 12, x_pos + tw + 16, y_pos + 40 + 12],
                               fill=(0, 0, 0, 180))
                draw.text((x_pos, y_pos), active_text, font=font, fill=(255, 255, 255))
                
            else:  # clean
                y_pos = int(h * 0.85)
                font = font_small
                bbox = draw.textbbox((0, 0), active_text, font=font)
                tw = bbox[2] - bbox[0]
                x_pos = (w - tw) // 2
                
                # Subtle outline
                for dx, dy in [(-2,-2),(-2,2),(2,-2),(2,2)]:
                    draw.text((x_pos + dx, y_pos + dy), active_text, font=font, fill=(0, 0, 0, 100))
                draw.text((x_pos, y_pos), active_text, font=font, fill=(255, 255, 255))
        
        # Add watermark: "AutoEdit" top-right
        wm_text = "AutoEdit"
        draw.text((w - 140, 20), wm_text, font=font_small, fill=(255, 255, 255, 180))
        
        img.save(f"{frames_dir}/{frame_file}")
    
    # Reconstruct
    subprocess.run([
        "ffmpeg","-y","-framerate","30","-i",f"{frames_dir}/frame_%05d.png",
        "-i",str(input_path),"-map","0:v","-map","1:a",
        "-c:v","libx264","-preset","fast","-crf","23",
        "-c:a","copy","-pix_fmt","yuv420p","-shortest", str(output_path)
    ], capture_output=True, timeout=120)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    return os.path.exists(output_path)

def edit_video():
    data = request.get_json(force=True) or {}
    path = data.get("path", "")
    if not path or not os.path.exists(path):
        return _err("file not found")
    
    remove_sil = data.get("removeSilences", True)
    auto_caps = data.get("autoCaptions", True)
    style = data.get("captionStyle", "tiktok")
    
    original_dur = get_duration(path)
    
    # Step 1: Remove silences if requested
    temp = EXPORTS / ("temp_" + str(int(time.time())) + ".mp4")
    current = Path(path)
    if remove_sil:
        ok = remove_silences(current, temp)
        if ok and temp.exists():
            current = temp
            # Recalculate original duration based on trimmed audio
            original_dur = get_duration(current)
    
    # Step 2: Burn captions
    out = EXPORTS / ("export_" + str(int(time.time())) + ".mp4")
    if auto_caps:
        try:
            segments, full_text = transcribe_video(current)
            ok = burn_captions_from_whisper(current, out, segments, style)
            if not ok:
                # Fallback: just copy (use -shortest to respect trimmed audio)
                subprocess.run(["ffmpeg","-y","-i",str(current),"-c","copy","-shortest",str(out)], capture_output=True, timeout=30)
        except Exception as e:
            print(f"Whisper/caption error: {e}")
            subprocess.run(["ffmpeg","-y","-i",str(current),"-c","copy","-shortest",str(out)], capture_output=True, timeout=30)
    else:
        subprocess.run(["ffmpeg","-y","-i",str(current),"-c","copy","-shortest",str(out)], capture_output=True, timeout=30)
    
    if not out.exists():
        return _err("export failed")
    
    final_dur = get_duration(out)
    return _ok({
        "output": str(out),
        "originalDuration": round(original_dur, 2),
        "finalDuration": round(final_dur, 2),
        "timeSaved": round(original_dur - final_dur, 2),
        "silencesRemoved": remove_sil,
        "captionsApplied": auto_caps,
    })

@app.route("/api/download")
def download():
    path = request.args.get("path", "")
    if not path or not os.path.exists(path):
        return _err("file not found", 404)
    return send_file(path, as_attachment=True)

# ════════════════════════════════════════════════════════════════
#  START
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true", help="Run production server")
    parser.add_argument("--port", default=5001, type=int)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    if args.server:
        app.run(host=args.host, port=args.port, threaded=True, debug=False)

# Transcript cache
_TRANSCRIPT_CACHE = {}
