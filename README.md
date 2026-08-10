# 🎬 Pixelab — AI-Powered Video Short Generator & Automatic Editor

Pixelab is an advanced, high-performance web application built with **Streamlit**, **MoviePy**, **OpenCV**, **Groq AI (LLM + Vision)**, and **Pexels HD Video API**. It turns user-uploaded audio voiceovers into fully rendered, professional video shorts with **kinetic subtitles**, **color grading**, **Ken Burns motion**, **cinematic transitions**, and **visual stock clips**—completely automated.

---

## 🤖 AI Director Settings & Intelligence Engine

The **AI Director (`modules/ai_director.py`)** acts as the executive producer and visual director for your video shorts using **Groq LLM (`openai/gpt-oss-120b` with `llama-3.3-70b-versatile` fallback)**.

### 🎭 1. Script Tone Profiles
You can select the script tone in the sidebar to shape how the AI Director structures visual search queries, expected visuals, and kinetic subtitle emphasis:

- 🎬 **Cinematic & Epic**: Dramatic, high-tension visual queries (e.g. *"storm clouds rising over mountain ridge"*).
- 📜 **Documentary**: Factual, measured, high-budget broadcast style.
- 🔥 **Motivational**: High-energy, action-driven, inspiring visuals.
- 📰 **News Style**: Crisp, objective, journalistic scene descriptions.
- 📖 **Story Narrative**: Character-driven, emotional visual framing.
- 💡 **Educational**: Simple, clear, explanatory visual cues.
- 🎭 **Dramatic**: High-stakes suspenseful framing.

### 🌐 2. Script Language & 100% English Subtitle Translation
Pixelab supports multi-lingual voiceover inputs:
- Supported Speech/Script Languages: **English, Hindi, Hinglish, Spanish, French, German, Arabic**.
- **Universal English Kinetic Subtitles**: Regardless of the voiceover speech language (e.g., Hindi or Hinglish voiceover), the AI Director automatically translates and formats **100% clean English kinetic subtitles** (`english_subtitle`) so your shorts perform globally on YouTube, Instagram, and TikTok!

### 📋 3. 2-Pass AI Director Storyboarding Pipeline
1. **Pass 1 — One-Time Video Brief Generation (`generate_video_brief`)**:
   - Locks the global **Topic** (e.g. *"Mars Atmosphere"*), **Purpose**, **Tone**, **Visual Style**, and **Things to Avoid** (e.g. *"avoid cigarette smoke or urban streets"*).
2. **Pass 2 — Batch Scene Analysis (`analyze_transcript`)**:
   - Processes all scene narrations in a single batch Groq LLM API call.
   - Generates 3–5 keyword visual search queries (`search_query` & `alt_queries`).
   - Automatically cleans noise words like *"4K"*, *"HD"*, *"video of"*, *"footage of"* via `clean_stock_query()`.
   - Generates **Expected Visual Descriptions** for real-time Vision AI verification (`qwen/qwen3.6-27b`).
   - Identifies **Emphasis Words & Numbers** for active spring-zoom animation.
   - Generates optional lower-third **AI Fact Cards & Stat Callouts** and **AI Map Locations**.

---

## ✨ Full Feature Overview

- 🎤 **Audio-First Workflow**: Upload any voiceover (`MP3`, `WAV`, `M4A`, `OGG`, `FLAC`, `AAC`) up to 200 MB.
- 🎙️ **4-Tier Speech-to-Text**: ElevenLabs STT API (`scribe_v1`) $\to$ Groq Whisper Cloud API $\to$ Local Whisper $\to$ Linear Interpolation.
- 👁️ **Groq Vision AI Visual Verification (`qwen/qwen3.6-27b`)**: Evaluates Pexels video candidate thumbnails in real-time to pick the highest visual quality clip.
- 💬 **Kinetic Subtitles & 10 Typography Packages**:
  - 🔥 **Hormozi Kinetic**, 💥 **MrBeast Impact**, ⚡ **Cyberpunk Glitch**, ✨ **Opus Glow**, 🍿 **Cinema Minimalist**, 🗯️ **Comic Boom**, 📰 **News Ticker**, 🎤 **Karaoke Wave**, 🔮 **Neon Synthwave**, ⌨️ **Typewriter Retro**.
- 🍿 **Cinematic Master Bundles & Color Grading**:
  - Hollywood Teal & Orange, Cyan/Orange split-toning, Warm halation, Anamorphic lens flare.
- 🔀 **Cinematic Transitions**: Whip Pan, Zoom Blur, Fade In/Out.
- 🎯 **AI Smart Auto-Framing**: Intelligent center/subject tracking for 16:9 ↔ 9:16 portrait re-framing.
- ⚡ **10x Speed Optimization**: Downloads 1080p Full HD clips (3–5 MB) instead of massive 100 MB 4K files.
- 🎤 **Lossless Direct Audio Muxing**: Attach uploaded voiceover directly via lossless FFmpeg multiplexing.

---

## 🚀 Quick Start & Installation

```bash
# Clone Repository
git clone https://github.com/kajalsingh748927-debug/pixellab.git
cd pixellab

# Install Dependencies
pip install -r requirements.txt

# Create .env File
GROQ_API_KEY=gsk_your_groq_api_key_here
PEXELS_API_KEY=your_pexels_api_key_here
ELEVENLABS_API_KEY=sk_your_elevenlabs_api_key_here

# Run Streamlit App
python -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser!

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
