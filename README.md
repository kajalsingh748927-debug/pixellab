# 🎬 Pixelab — AI-Powered Video Generator & Automated Editor

Pixelab is an advanced, high-performance web application built with **Streamlit**, **MoviePy**, **OpenCV**, **Groq AI (LLM + Vision)**, and **Pexels HD Video API**. It turns user-uploaded audio voiceovers into fully rendered, professional video shorts with **kinetic subtitles**, **color grading**, **Ken Burns motion**, **cinematic transitions**, and **visual stock clips**—completely automated.

---

## ✨ Features & Highlights

- 🎤 **Audio-First Workflow**: Upload any voiceover (`MP3`, `WAV`, `M4A`, `OGG`, `FLAC`, `AAC`) up to 200 MB.
- 🎙️ **4-Tier Speech-to-Text**:
  1. **ElevenLabs STT API** (`scribe_v1`) — Ultra-accurate word timestamps.
  2. **Groq Whisper API** (`whisper-large-v3-turbo`) — Free, cloud-hosted (0 MB local RAM).
  3. **Local OpenAI Whisper** — Automatic fallback if installed.
  4. **Linear Timestamp Interpolation** — Fallback guarantee.
- 🤖 **AI Director & Storyboard Generator (Groq LLM)**: Automatically creates visual briefs, search queries, visual expected descriptions, and 100% English kinetic subtitles.
- 👁️ **Groq Vision AI Visual Verification (`qwen/qwen3.6-27b`)**: Evaluates Pexels video candidate thumbnails in real-time to pick the highest visual quality clip.
- 💬 **Kinetic Subtitles & 10 Typography Packages**:
  - 🔥 **Hormozi Kinetic** (Yellow active glow, scale pop, bold text)
  - 💥 **MrBeast Impact** (Spring bounce, dual-color stroke)
  - ⚡ **Cyberpunk Glitch** (Cyan & magenta glitch outlines)
  - ✨ **Opus Glow**, 🍿 **Cinema Minimalist**, 🗯️ **Comic Boom**, 📰 **News Ticker**, 🎤 **Karaoke Wave**, 🔮 **Neon Synthwave**, ⌨️ **Typewriter Retro**.
- 🍿 **Cinematic Master Bundles & Color Grading**:
  - Teal & Orange 3-way primary grade, Cyan/Orange split-toning, Warm halation, Anamorphic lens flare.
- 🔀 **Cinematic Transitions**: Whip Pan, Zoom Blur, Fade In/Out.
- 🎯 **AI Smart Auto-Framing**: Intelligent center/subject tracking for 16:9 ↔ 9:16 portrait re-framing.
- ⚡ **10x Speed Optimization**: Downloads 1080p Full HD clips (3–5 MB) instead of massive 100 MB 4K files.
- 🎤 **Lossless Direct Audio Muxing**: Attach uploaded voiceover directly via lossless FFmpeg multiplexing.

---

## 🏗️ Architecture & Pipeline Flow

```
User Audio Upload (.mp3 / .wav)
       │
       ▼
1. Transcribe Engine (ElevenLabs → Groq Whisper → Fallback)
       │
       ▼
2. Scene Splitter (Divides word timestamps into N scenes)
       │
       ▼
3. AI Director (Groq LLM generates search queries + English subtitles)
       │
       ▼
4. Stock Fetcher & Vision Selector (Pexels HD Video + Groq Vision AI)
       │
       ▼
5. Compositor Render Engine (OpenCV subtitles + VFX + Color Grade + Transitions)
       │
       ▼
6. FFmpeg Direct Audio Muxing → final_video.mp4
       │
       ▼
st.video() + st.download_button()  (Download Result)
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher
- FFmpeg installed and added to system `PATH`

### 2. Clone Repository
```bash
git clone https://github.com/kajalsingh748927-debug/pixellab.git
cd pixellab
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
ELEVENLABS_API_KEY=sk_your_elevenlabs_api_key_here
```

### 5. Run the Application
```bash
python -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser!

---

## 🐳 Docker & Cloud Deployment (Render.com)

The project includes a `Dockerfile` and `render.yaml` configured for Docker deployment:

### Build Docker Image Locally:
```bash
docker build -t pixellab .
docker run -p 8501:8501 --env-file .env pixellab
```

### Render Deployment Configuration (`render.yaml`):
```yaml
services:
  - type: web
    name: pixelab
    env: docker
    dockerfilePath: ./Dockerfile
```

---

## 📁 Repository Structure

```
pixellab/
├── app.py                      # Main Streamlit entry point
├── config.py                   # Environment config, paths, resolution settings
├── Dockerfile                  # Production Docker container definition
├── render.yaml                 # Render cloud deployment config
├── requirements.txt            # Python dependencies
├── ui/
│   ├── page.py                 # Audio upload, live preview, main page layout
│   ├── sidebar.py              # User controls (aspect ratio, FPS, presets, VFX)
│   └── progress_tracker.py     # Real-time render dashboard & scene table UI
└── modules/
    ├── transcribe_engine.py    # 4-tier speech-to-text transcription engine
    ├── scene_splitter.py       # Timestamp-based scene splitter
    ├── ai_director.py          # Groq LLM script analyzer & search query generator
    ├── stock_fetcher.py        # Pexels HD video candidate downloader & cache
    ├── video_selector.py       # Groq Vision AI visual verification selector
    ├── compositor.py           # Master video assembly & rendering engine
    ├── subtitle_vfx.py         # Kinetic subtitle & OpenCV frame renderer
    ├── subtitle_packages.py    # Preset typography definitions (Hormozi, MrBeast, etc.)
    ├── cinematic_packages.py   # Color grade LUTs & cinematic style bundles
    ├── transitions.py          # Whip pan, zoom blur, fade transition effects
    ├── auto_framing.py         # AI smart crop & aspect ratio re-framer
    └── cache_manager.py        # DiskCache manager for video clips & thumbnails
```

---

## 📜 License
MIT License. Free for commercial and non-commercial use.
