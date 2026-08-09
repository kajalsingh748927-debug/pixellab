"""
app.py — Pixelab Entry Point
─────────────────────────────────────────────────────────────────────────────
Thin Streamlit entry point.  All UI logic lives in ui/ and all video
processing logic lives in modules/.  This file only:
  1. Configures the Streamlit page
  2. Loads & resolves API keys (env → st.secrets fallback)
  3. Calls sidebar.render_sidebar() and page.render_page()
─────────────────────────────────────────────────────────────────────────────
"""
# ── Ensure UTF-8 output encoding on Windows ────────────────────────────────
import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
# ───────────────────────────────────────────────────────────────────────────

import streamlit as st
from config import (
    GROQ_API_KEY, ELEVENLABS_API_KEY,
    PEXELS_API_KEY,
)
from ui.sidebar import render_sidebar
from ui.page    import render_page

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Pixelab - AI Video Generator",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Pixelab — AI Video Generator")
st.caption("Generate cinematic HD short videos with full professional controls.")

# ── Resolve API Keys ─────────────────────────────────────────
active_keys = {
    "GROQ_API_KEY":       GROQ_API_KEY,
    "PEXELS_API_KEY":     PEXELS_API_KEY,
    "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
}

try:
    for key in active_keys:
        if key in st.secrets:
            active_keys[key] = st.secrets[key]
except Exception:
    pass

# ── Show missing-key warnings ────────────────────────────────
if not active_keys["GROQ_API_KEY"]:
    st.error("🔑 GROQ_API_KEY is missing! Add it to .env")
if not active_keys["PEXELS_API_KEY"]:
    st.error("🔑 PEXELS_API_KEY is missing! Add it to .env")

keys_ready = bool(active_keys["GROQ_API_KEY"] and active_keys["PEXELS_API_KEY"])

# ── Render Sidebar + Main Page ───────────────────────────────
sidebar_data = render_sidebar()
render_page(sidebar_data, active_keys, keys_ready)
