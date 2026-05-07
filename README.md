# AutoEdit v3.3

AI-powered video editor that actually works. Upload a video, pick a style, get TikTok-ready output.

**Demo:** [https://empty-llamas-argue.loca.lt](https://empty-llamas-argue.loca.lt) (localtunnel — temporary)

---

## Features

| Feature | How it works |
|---|---|
| **🤖 Whisper AI** | OpenAI Whisper transcribes speech → accurate captions |
| **✂️ Silence removal** | Auto-cuts dead air using ffmpeg concat |
| **🎨 5 Caption Styles** | TikTok glow, YouTube bar, Neon, Cinematic, Clean |
| **📊 Progress tracking** | Poll `/api/progress/<job_id>` for real-time status |
| **🔄 Retry** | Auto-retry ffmpeg on transient failures |

---

## Quick Start

```bash
git clone https://github.com/reviewmobsales-debug/autoedit-v3.git
cd autoedit-v3
python3 -m pip install -r requirements.txt
python3 main.py --server --port 5002
# Open http://localhost:5002
```

---

## API

### Upload
```bash
curl -X POST http://localhost:5002/api/upload -F "file=@video.mp4"
```

### Edit
```bash
curl -X POST http://localhost:5002/api/edit \
  -H "Content-Type: application/json" \
  -d '{"path":"/path/to/upload.mp4","removeSilences":true,"autoCaptions":true,"captionStyle":"tiktok"}'
```

### Progress
```bash
curl http://localhost:5002/api/progress/<job_id>
```

### Download
```bash
curl "http://localhost:5002/api/download?path=/path/to/export.mp4" -o result.mp4
```

---

## Caption Styles

| Style | Preview | Best for |
|---|---|---|
| **TikTok** | Pink glow + pill background | Vertical 9:16 viral clips |
| **YouTube** | Bottom bar + shadow | Educational/tutorials |
| **Neon** | Cyan glow + dark box | Gaming/tech content |
| **Cinematic** | Letterbox + gold uppercase | Movie trailers |
| **Clean** | White text + subtle stroke | Professional/corporate |

---

## Deploy

### Render (recommended — free)
1. Push repo to GitHub
2. Go to [dashboard.render.com](https://dashboard.render.com)
3. Create Web Service → connect repo
4. Build: `pip install -r requirements.txt`
5. Start: `python main.py --server --host 0.0.0.0`
6. Done — permanent URL generated

### Docker
```bash
docker build -t autoedit .
docker run -p 8080:10000 autoedit
```

### Fly.io
```bash
fly deploy --dockerfile Dockerfile
```

---

## Architecture

```
autoedit-v3/
├── main.py              # Flask app + HTML UI
├── editor/
│   ├── captions.py     # PIL-based caption rendering (5 styles)
│   └── effects.py      # Silence removal, face crop
├── requirements.txt
├── Dockerfile
├── railway.toml
└── fly.toml
```

---

## License

MIT — Built by ReviewMob for ReviewMob.
