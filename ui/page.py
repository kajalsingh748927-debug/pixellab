"""
ui/page.py
─────────────────────────────────────────────────────────────────────────────
Main page layout for Pixelab — Audio-First Workflow.
Upload your audio voiceover (MP3 / WAV / M4A / OGG / FLAC / AAC).
Whisper AI transcribes the audio, extracts word-level timestamps, and syncs
kinetic subtitles + Pexels HD video cuts to your voice.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import time
import numpy as np
import streamlit as st

from modules.ai_director  import analyze_transcript, generate_video_brief
from modules.compositor   import build_master_video, build_master_video_from_audio
from modules.transcribe_engine import transcribe_audio
from modules.scene_splitter    import split_into_scenes
from modules.subtitle_vfx      import generate_live_preview_frame
from ui.progress_tracker  import ProgressTracker
from config import OUTPUT_DIR, TEMP_DIR


def _inject_api_keys(keys: dict):
    """Push active API keys into os.environ so modules can read them."""
    for env_name, value in keys.items():
        if value:
            os.environ[env_name] = value


def _save_uploaded_audio(uploaded_file) -> str | None:
    """
    Saves a Streamlit UploadedFile with file validation, filename sanitization, and disk quota monitoring.
    Returns the absolute file path on success, or None on failure.
    """
    from modules.error_handler import validate_uploaded_file, sanitize_filename, auto_purge_temp_dir

    is_valid, err_msg = validate_uploaded_file(uploaded_file, max_size_mb=200.0)
    if not is_valid:
        st.error(err_msg)
        return None

    # Auto-purge old temp files if disk quota exceeds 500 MB
    auto_purge_temp_dir(TEMP_DIR, max_mb=500.0)

    try:
        clean_name = sanitize_filename(uploaded_file.name)
        ext = os.path.splitext(clean_name)[-1].lower() or ".mp3"
        save_path = os.path.join(OUTPUT_DIR, f"uploaded_audio{ext}")
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return save_path
    except Exception as e:
        st.error(f"❌ Failed to save uploaded audio safely: {e}")
        return None


def _render_live_preview_section(video_config: dict, api_keys: dict):
    """
    Renders an interactive Live Preview panel for Subtitles, Fact Cards, Intro Cards, Chapter Cards, and Outro Cards.
    Updates instantly (~10ms) whenever the user modifies sidebar settings.
    """
    with st.expander("👁️ Real-Time Live Style & Title Card Preview (Instant Updates)", expanded=True):
        preview_mode = st.radio(
            "Target Preview Mode:",
            ["💬 Kinetic Subtitles Pass", "📊 Fact Card / Text Overlay", "🎬 Intro Title Card", "📖 Chapter Title Card", "🎬 Outro CTA Card"],
            index=0,
            horizontal=True
        )

        col_img, col_ctrl = st.columns([1.6, 1])

        with col_ctrl:
            if preview_mode == "💬 Kinetic Subtitles Pass":
                st.markdown("##### ⚙️ Subtitle & Style Live Tester")
                test_text = st.text_input(
                    "💬 Custom Test Sentence:",
                    value="NEON CITIES ARE EXPANDING ACROSS THE WORLD TODAY 🔥",
                    help="Type any sentence to see font, size, position, active word glow, and emojis live."
                )
                words = [w for w in test_text.split() if w]
                max_idx = max(len(words), 1)
                if max_idx > 1:
                    active_idx = st.slider("Highlight Word Index", 1, max_idx, min(3, max_idx))
                else:
                    active_idx = 1

                st.caption(f"📐 **Ratio:** {video_config.get('aspect_ratio', '').split('(')[0].strip()}")
                st.caption(f"💬 **Package:** {video_config.get('subtitle_package', 'Custom')}")
                st.caption(f"🔤 **Letter Spacing:** {video_config.get('letter_spacing', 0)}px | **Word Spacing:** {video_config.get('word_spacing', 10)}px")
                st.caption(f"📍 **Position:** {video_config.get('position', 'Bottom')}")

            elif preview_mode == "📊 Fact Card / Text Overlay":
                st.markdown("##### 📊 Fact Card & Text Overlay Live Tester")
                fact_preview_text = st.text_input("💬 Sample Fact Text:", value="Light takes 8 minutes to travel from the Sun to Earth.")
                fact_preview_style = st.radio(
                    "Card Render Style:",
                    ["💬 Styled Text Only (No Box)", "📊 Infographic Stat Box"],
                    index=0,
                    horizontal=True
                )
                st.caption(f"🔤 **Font:** {video_config.get('fact_font_family', 'DejaVuSans-Bold.ttf')}")
                st.caption(f"📐 **Scale:** {video_config.get('fact_font_scale', 1.0)}x | **Position:** {video_config.get('fact_position', 'bottom').upper()}")
                st.caption(f"✨ **Anim:** {video_config.get('entrance_animation', 'tracking')} → {video_config.get('exit_animation', 'fade')}")

            elif preview_mode == "🎬 Intro Title Card":
                st.markdown("##### 🎬 Intro Card Live Tester")
                intro_title = st.text_input("Intro Title:", value="PIXELAB DEMO")
                intro_sub = st.text_input("Intro Subtitle Tagline:", value="THE ULTIMATE AI VIDEO GENERATOR")
                anim_t = st.slider("⏱️ Animation Scrubber (Time t in sec)", 0.0, 3.0, 0.8, 0.05, help="Scrub time to see entrance animation, tracking compression, and blur/glow reveal in real time!")
                st.caption(f"✨ **Anim Style:** {video_config.get('intro_style_override') or 'blur_to_sharp'}")
                st.caption(f"📐 **Tracking:** {video_config.get('intro_start_tracking', 24)}px ➔ {video_config.get('intro_end_tracking', 6)}px")

            elif preview_mode == "📖 Chapter Title Card":
                st.markdown("##### 📖 Chapter Card Live Tester")
                chapter_title = st.text_input("Chapter Title:", value="PART 1: THE REVOLUTION")
                anim_t = st.slider("⏱️ Animation Scrubber (Time t in sec)", 0.0, 2.5, 0.6, 0.05, help="Scrub time to see bracket draw, wipe, slide, blur, or neon trace animation in real time!")
                st.caption(f"✨ **Anim Style:** {video_config.get('chapter_card_style', 'bracket_frame')}")
                st.caption(f"📍 **Position:** {video_config.get('chapter_card_position', 'center')}")

            else:  # Outro CTA Card
                st.markdown("##### 🎬 Outro Card Live Tester")
                outro_thanks = st.text_input("Main Heading Text:", value=video_config.get("outro_thanks_text") or "THANKS FOR WATCHING!")
                outro_cta = st.text_input("CTA Subtitle Text:", value=video_config.get("outro_cta_override") or "LIKE & SUBSCRIBE FOR MORE")
                outro_channel = st.text_input("Channel Handle:", value=video_config.get("outro_channel_name", "@YourChannel"))
                anim_t = st.slider("⏱️ Animation Scrubber (Time t in sec)", 0.0, 4.0, 0.8, 0.05, help="Scrub time to see outro entrance, tracking, gradient fill, and pulsing button!")
                st.caption(f"✨ **Anim Style:** {video_config.get('outro_style_override') or 'blur_to_sharp'}")
                st.caption(f"📐 **Heading Scale:** {video_config.get('outro_font_scale', 1.1)}x | **CTA Scale:** {video_config.get('outro_cta_scale', 0.85)}x")

            # 3-Second Quick Clip Sampler
            if st.button("⚡ Render 3-Sec Quick Preview Clip", use_container_width=True, help="Renders a 3-second sample clip to preview motion, audio sync, and transitions in ~3s"):
                with st.spinner("⚡ Rendering 3-second sample clip..."):
                    _inject_api_keys(api_keys)
                    test_scenes = [{
                        "narration": "NEON CITIES ARE EXPANDING ACROSS THE WORLD TODAY",
                        "search_query": "futuristic city",
                    }]
                    preview_out = os.path.join(OUTPUT_DIR, "quick_preview.mp4")
                    cfg = dict(video_config)
                    cfg["enable_bg_music"] = False
                    success = build_master_video(test_scenes, cfg, output_filename="quick_preview.mp4")
                    if success and os.path.exists(preview_out):
                        st.session_state["quick_preview_video"] = preview_out
                        st.success("✅ 3-Second Sample Clip Ready!")
                    else:
                        st.error("⚠️ Quick preview generation notice — try regular video render.")

            if st.session_state.get("quick_preview_video") and os.path.exists(st.session_state["quick_preview_video"]):
                st.video(st.session_state["quick_preview_video"])

        with col_img:
            # Generate instant preview frame (~10ms)
            try:
                aspect = video_config.get("aspect_ratio", "16:9 Landscape (YouTube)")
                if "9:16" in aspect:
                    w_pv, h_pv = 540, 960
                elif "1:1" in aspect:
                    w_pv, h_pv = 640, 640
                else:
                    w_pv, h_pv = 960, 540

                bg_dummy = np.zeros((h_pv, w_pv, 3), dtype=np.uint8)
                bg_dummy[:, :] = (30, 40, 60)

                t_scrub = locals().get("anim_t", 0.8)

                if preview_mode == "📊 Fact Card / Text Overlay":
                    if "text only" in fact_preview_style.lower():
                        from modules.fact_text_overlay import apply_fact_text_overlay
                        f_cfg = dict(video_config)
                        f_cfg["fact_text"] = fact_preview_text
                        preview_frame = apply_fact_text_overlay(bg_dummy, 0.8, 2.5, f_cfg)
                    else:
                        from modules.subtitle_vfx import draw_fact_card_overlay
                        f_data = {"label": "KEY STATISTIC", "value": fact_preview_text}
                        preview_frame = draw_fact_card_overlay(bg_dummy, f_data, t=0.8, duration=2.5)

                elif preview_mode == "🎬 Intro Title Card":
                    from modules.title_overlay import apply_intro_overlay
                    idata = {"title": intro_title, "subtitle": intro_sub}
                    preview_frame = apply_intro_overlay(bg_dummy, t_scrub, idata, video_config)

                elif preview_mode == "📖 Chapter Title Card":
                    from modules.title_overlay import apply_chapter_overlay
                    preview_frame = apply_chapter_overlay(bg_dummy, t_scrub, chapter_title, video_config)

                elif preview_mode == "🎬 Outro CTA Card":
                    from modules.title_overlay import apply_outro_overlay
                    odata = {"thanks_text": outro_thanks, "cta_text": outro_cta, "channel_name": outro_channel}
                    preview_frame = apply_outro_overlay(bg_dummy, 3.2 + t_scrub, 4.0, odata, video_config)

                else:
                    preview_frame = generate_live_preview_frame(
                        video_config,
                        sample_text=test_text,
                        active_word_index=active_idx - 1
                    )

                st.image(
                    preview_frame,
                    caption=f"Live Preview | {preview_mode} | {video_config.get('aspect_ratio', '')}",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Preview render notice: {e}")

    st.divider()


def render_page(sidebar_data: dict, api_keys: dict, keys_ready: bool):
    """
    Renders the main page — Audio Upload & Video Generation.
    """
    from modules.session_persistence import load_project_checkpoint, save_project_checkpoint

    video_config  = sidebar_data["video_config"]
    scene_count   = sidebar_data["scene_count"]
    ai_tone       = sidebar_data["ai_tone"]
    fps_choice    = sidebar_data["fps_choice"]
    aspect_ratio  = sidebar_data["aspect_ratio"]
    color_grade   = sidebar_data["color_grade"]
    sub_style     = sidebar_data["sub_style"]

    # ── Auto-restore session from disk checkpoint on browser refresh ─────────
    if "checkpoint_restored" not in st.session_state:
        st.session_state["checkpoint_restored"] = True
        ckpt = load_project_checkpoint()
        if ckpt.get("scenes") or ckpt.get("script_text"):
            st.session_state["saved_checkpoint"] = ckpt
            if ckpt.get("audio_path") and os.path.exists(ckpt["audio_path"]):
                st.session_state["current_audio_file"] = os.path.basename(ckpt["audio_path"])
            if ckpt.get("script_text"):
                st.session_state["transcript_result"] = {
                    "full_text": ckpt["script_text"],
                    "word_timestamps": [],
                    "total_duration": 10.0
                }

    # ── Real-Time Live Visual & Subtitle Preview Engine ───────────────────────
    _render_live_preview_section(video_config, api_keys)

    # ════════════════════════════════════════════════════════════════════════
    # AUDIO UPLOAD WORKFLOW
    # ════════════════════════════════════════════════════════════════════════
    st.markdown(
        "### 🎤 Upload Your Audio Voiceover\n"
        "Upload a pre-recorded MP3, WAV, M4A, OGG, or FLAC audio file. "
        "Whisper AI transcribes your voice, extracts word-level timestamps, "
        "and syncs kinetic subtitles + Pexels HD video cuts to your narration."
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "🎵 Audio File (MP3 / WAV / M4A / OGG / FLAC / AAC — max 200 MB)",
            type=["mp3", "wav", "m4a", "ogg", "flac", "aac"],
            help="Your voiceover audio will be used as-is in the final video.",
        )

    with col2:
        st.markdown("**⚙️ Quick Settings**")
        st.caption(f"📐 {aspect_ratio.split('(')[0].strip()}")
        st.caption(f"🎨 Grade: {color_grade}")
        st.caption(f"💬 Style: {sub_style}")
        st.caption(f"🤖 Tone: {ai_tone}")
        st.caption(f"🎬 Scenes: {scene_count}")

    groq_key = api_keys.get("GROQ_API_KEY", "") or os.environ.get("GROQ_API_KEY", "")

    if uploaded_file is not None:
        _inject_api_keys(api_keys)
        audio_path = _save_uploaded_audio(uploaded_file)

        # ── STAGE 1: AUTOMATIC TRANSCRIPTION & EXTRACTION REVIEW ─────────────
        if audio_path and ("current_audio_file" not in st.session_state or st.session_state["current_audio_file"] != uploaded_file.name):
            st.session_state["current_audio_file"] = uploaded_file.name
            st.session_state["extraction_approved"] = False
            with st.spinner("🎙️ Transcribing audio & extracting title/facts with Groq AI..."):
                st.session_state["transcript_result"] = transcribe_audio(audio_path)

        t_res = st.session_state.get("transcript_result", {})
        full_text       = t_res.get("full_text", "")
        word_timestamps = t_res.get("word_timestamps", [])
        total_duration  = t_res.get("total_duration", 0.0)
        method          = t_res.get("method", "whisper")
    else:
        full_text = "Light takes 8 minutes and 20 seconds to travel from the Sun to Earth, traveling at 299,792 km/s across 149.6 million km."
        word_timestamps = []
        total_duration = 10.0

    # ── ALWAYS RENDER THE EDITABLE FACT & CARD MANAGER PANEL ────────────────
    from ui.extraction_review import render_extraction_review_panel
    review_data = render_extraction_review_panel(full_text, word_timestamps=word_timestamps, api_key=groq_key)

    if review_data.get("title"):
        video_config["intro_title_override"] = review_data["title"]

    is_processing = st.session_state.get("is_rendering", False)
    render_disabled = is_processing or not keys_ready or (uploaded_file is None)
    render_tooltip  = (
        "Video rendering in progress..." if is_processing
        else "Upload an audio file first." if uploaded_file is None
        else "API keys missing." if not keys_ready
        else ""
    )

    col_ub1, col_ub2 = st.columns([1, 1])
    with col_ub1:
        q_label = "⏳ Processing Clip..." if is_processing else "⚡ TEST 3-SEC SAMPLE VIDEO"
        btn_u_quick = st.button(
            q_label,
            type="secondary",
            disabled=(uploaded_file is None or is_processing),
            use_container_width=True,
            help="Renders a 3-second sample clip using your uploaded audio"
        )
    with col_ub2:
        f_label = "⏳ Video Rendering In Progress..." if is_processing else "🚀 RENDER FULL VIDEO WITH UPLOADED AUDIO"
        btn_u_full = st.button(
            f_label,
            type="primary",
            disabled=render_disabled,
            use_container_width=True,
            help=render_tooltip,
        )

    if btn_u_full:
        # Throttle & Debounce protection
        now = time.time()
        if now - st.session_state.get("last_click_time", 0) < 0.8:
            st.warning("⚠️ Action throttled — please wait a moment.")
            return
        st.session_state["last_click_time"] = now
        st.session_state["extraction_approved"] = True
        st.session_state["is_rendering"] = True

    run_u_quick = btn_u_quick or st.session_state.pop("trigger_quick_test", False)
    if run_u_quick:
        now = time.time()
        if now - st.session_state.get("last_click_time", 0) < 0.8:
            st.warning("⚠️ Action throttled — please wait a moment.")
            return
        st.session_state["last_click_time"] = now
        st.session_state["is_rendering"] = True

    # GATEWAY CHECK: If quick test isn't requested and user hasn't approved yet, STOP HERE!
    if not run_u_quick and not st.session_state.get("extraction_approved"):
        st.info("👆 **Review your Title & Facts above.** Click **'✅ Approve — Looks Good'** or **'🚀 RENDER FULL VIDEO'** to start scene creation & video generation!")
        return

    try:
        # ── STAGE 2: APPROVED! SCENE BREAKDOWN & VIDEO GENERATION ────────────
        progress_bar = st.progress(0.0)
        status_box = st.info("🎬 Step 1/4 — Script Approved! Splitting audio into scenes...")
        progress_bar.progress(0.18)

        scenes = split_into_scenes(word_timestamps, total_duration, scene_count)

        # ── AI Director (search queries only) ─────────────────────────────
        status_box.info(
            f"🤖 Step 3/4 — AI Director generating search queries for {len(scenes)} scenes..."
        )
        progress_bar.progress(0.22)

        groq_key = api_keys.get("GROQ_API_KEY", "")
        video_brief = generate_video_brief(full_text, groq_key)

        scenes = analyze_transcript(
            scenes,
            groq_key,
            tone=video_config["ai_tone"],
            video_brief=video_brief,
        )

        # Attach extracted Intro Title & Facts to scenes for real-time tracking display
        if scenes:
            override_title = video_config.get("intro_title_override") or full_text[:40]
            scenes[0]["intro"] = {"title": override_title, "style": video_config.get("preset_name", "🎬 Cinematic Warm")}

            # Attach approved facts to subsequent scenes based on chosen card_style
            facts_list = review_data.get("facts", []) if 'review_data' in locals() else []
            for idx, fact in enumerate(facts_list):
                scene_idx = idx + 1
                if scene_idx < len(scenes):
                    c_style = str(fact.get("card_style", "")).lower()
                    if "text only" in c_style:
                        scenes[scene_idx]["fact_text"] = fact.get("text", "")
                        scenes[scene_idx]["display_duration"] = fact.get("display_duration", 2.5)
                    elif "stat box" in c_style or "infographic" in c_style:
                        scenes[scene_idx]["fact_card"] = {
                            "stat_value": fact.get("text", ""),
                            "label": fact.get("category", "FACT").upper(),
                            "confidence": fact.get("confidence", "high")
                        }
                    elif "chapter" in c_style:
                        scenes[scene_idx]["show_chapter"] = True
                        scenes[scene_idx]["chapter_title"] = fact.get("text", "")

        progress_bar.progress(0.28)
        save_project_checkpoint(video_config, scenes, full_text, audio_path)
        status_box.success(
            f"✅ Ready! {len(scenes)} scenes | {total_duration:.1f}s audio | "
            f"Starting video render..."
        )

        # Show scene breakdown before render
        with st.expander("🎬 Scene Breakdown", expanded=False):
            for i, sc in enumerate(scenes, start=1):
                st.markdown(
                    f"**Scene {i}** ({sc['start_sec']:.1f}s – {sc['end_sec']:.1f}s, "
                    f"{sc['end_sec']-sc['start_sec']:.1f}s) | "
                    f"🔍 `{sc['search_query']}` | "
                    f"*\"{sc['narration'][:80]}...\"*"
                )

        # ── Phase: Build video ─────────────────────────────────────────────
        tracker = ProgressTracker(scene_count)

        c1, c2, c3, c4, c5 = st.columns(5)
        tracker.done_metric    = c1.empty()
        tracker.fail_metric    = c2.empty()
        tracker.pend_metric    = c3.empty()
        tracker.elapsed_metric = c4.empty()
        tracker.eta_metric     = c5.empty()
        tracker.tracker_ph     = st.empty()
        tracker.progress_bar   = progress_bar
        tracker.status_box     = status_box
        tracker._update_metrics(done=0, failed=0, left=scene_count, elapsed=0, eta="—")

        callback = tracker.make_callback()
        out_path = os.path.join(OUTPUT_DIR, "final_video.mp4")
        t0       = time.time()

        success = build_master_video_from_audio(
            scenes=scenes,
            uploaded_audio_path=audio_path,
            config=video_config,
            output_filename="final_video.mp4",
            progress_callback=callback,
        )

        total_time = time.time() - t0
        tracker.show_result(
            success=success and os.path.exists(out_path),
            out_path=out_path if success else None,
            total_time=total_time,
            scenes=scenes,
        )
    except Exception as render_error:
        from modules.error_handler import handle_exception
        err_info = handle_exception(render_error, context_name="Video Render Pipeline")
        st.error(f"❌ **Render Pipeline Error**: {err_info['user_message']}")
        with st.expander("🔍 Detailed Stacktrace (For Debugging)", expanded=False):
            st.code(err_info['traceback'], language="python")
    else:
        st.toast("🎉 Video production completed successfully!", icon="🎬")
    finally:
        # Re-enable buttons after rendering completes
        st.session_state["is_rendering"] = False
