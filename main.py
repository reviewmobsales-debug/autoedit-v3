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

# Modular imports
from editor.effects import get_duration, remove_silences
from editor.captions import burn_captions_from_whisper
from editor.transcription import transcribe_video
from burn_overlay import burn_text_overlay


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
    return segments, result["text"]



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


@app.route("/api/analyze", methods=["POST"])
def analyze_video_endpoint():
    """Upload and analyze video orientation/format."""
    vid = request.files.get("file")
    if not vid or vid.filename == "":
        return _err("no file")
    
    import tempfile, subprocess, json
    fd, temp_path = tempfile.mkstemp(suffix=".mp4")
    os.close(fd)
    vid.save(temp_path)
    
    # Analyze
    r = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "json", temp_path
    ], capture_output=True, text=True, timeout=10)
    
    os.remove(temp_path)
    
    try:
        data = json.loads(r.stdout)
        s = data.get("streams", [{}])[0]
        w, h = s.get("width", 0), s.get("height", 0)
        dur = float(s.get("duration", 0))
        aspect = w / h if h else 0
        
        if aspect < 0.8:
            orient, best_for = "VERTICAL", ["TikTok", "Reels", "Shorts"]
            style = "tiktok"
        elif aspect > 1.5:
            orient, best_for = "HORIZONTAL", ["YouTube", "Landscape"]
            style = "youtube"
        else:
            orient, best_for = "SQUARE", ["Instagram", "Facebook"]
            style = "clean"
        
        return _ok({
            "width": w, "height": h, "aspect_ratio": round(aspect, 2),
            "duration": round(dur, 1), "orientation": orient,
            "best_for": best_for, "suggested_style": style
        })
    except Exception as e:
        return _err(f"analyze error: {e}")

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
