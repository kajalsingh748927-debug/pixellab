"""
ui/sidebar.py
─────────────────────────────────────────────────────────────────────────────
All sidebar controls for Pixelab.
Call `render_sidebar()` once from app.py — it draws the sidebar and returns
the complete video_config dictionary plus scene_count and word_length.
─────────────────────────────────────────────────────────────────────────────
"""
import streamlit as st
from modules.cinematic_packages import get_cinematic_package, CINEMATIC_PACKAGES



DURATION_MAP = {
    "✨ Dynamic Script Pacing (Auto Duration & Scenes)": ("AUTO", "Auto Pacing"),
    "15 Seconds (2 Scenes)":   (2, "6 to 10 words"),
    "30 Seconds (4 Scenes)":   (4, "8 to 12 words"),
    "45 Seconds (6 Scenes)":   (6, "10 to 14 words"),
    "60 Seconds (8 Scenes)":   (8, "12 to 18 words"),
    "5 Minutes (20 Scenes)":   (20, "15 to 25 words"),
    "10 Minutes (40 Scenes)":  (40, "20 to 30 words"),
    "15 Minutes (60 Scenes)":  (60, "20 to 30 words"),
    "30 Minutes (120 Scenes)": (120, "25 to 35 words"),
    "40 Minutes (160 Scenes)": (160, "25 to 35 words"),
}


def render_sidebar() -> dict:
    """
    Draws the full sidebar and returns a config dict with keys:
        video_config, scene_count, word_length, video_duration, audio_mode
    """
    # Read audio mode set by page.py (so sidebar can hide irrelevant controls)
    audio_mode = "🎤 Upload Your Own Audio"
    is_upload_mode = True

    with st.sidebar:

        # ── Persistent 3-Sec Test Button ──────────────────────
        st.markdown("### ⚡ Quick Test & Preview")
        if st.button("⚡ Test 3-Sec Sample Video", use_container_width=True, help="Render a 3-second sample video testing all current settings at any time!"):
            st.session_state["trigger_quick_test"] = True
        st.divider()

        # ── 1. VIDEO LAYOUT ──────────────────────────────────
        st.header("📐 Video Layout")


        aspect_ratio = st.selectbox(
            "Aspect Ratio",
            [
                "16:9 Landscape (YouTube)",
                "9:16 Portrait (Reels/Shorts)",
                "1:1 Square (Instagram)",
                "4:3 Classic",
                "2.35:1 Cinematic Ultrawide",
            ],
            index=0,
        )

        resolution = st.selectbox(
            "Resolution",
            [
                "3840×2160 (4K Ultra HD)",
                "2160×3840 (4K Portrait)",
                "1920×1080 (Full HD)",
                "1280×720 (HD)",
                "1080×1920 (Portrait FHD)",
                "1080×1080 (Square)",
            ],
            index=2,
        )

        fps_choice = st.select_slider(
            "Frame Rate (FPS)", options=[24, 30, 60], value=24
        )

        video_duration = st.selectbox(
            "Video Duration & Pacing",
            list(DURATION_MAP.keys()),
            index=0,
            help="Dynamic Script Pacing automatically breaks your script into natural scenes and matches the exact voiceover length!"
        )


        encoder_choice = st.selectbox(
            "⚡ Hardware Encoder",
            [
                "CPU (libx264 — Universal)",
                "NVIDIA NVENC (Ultra Fast GPU)",
                "Intel QuickSync (GPU/iGPU)",
            ],
            index=0,
            help="CPU works on every machine. NVENC/QuickSync are 5-10× faster but require NVIDIA/Intel GPU drivers. If GPU fails, the system auto-falls back to CPU."
        )

        st.divider()

        # ── 2. CINEMATIC STYLE & PACKAGES ─────────────────────
        st.header("🍿 Cinematic Style & Lighting")

        cinematic_package = st.selectbox(
            "1-Click Cinematic Master Bundle",
            [
                "Custom (Manual Overrides)",
                "🎬 Hollywood Blockbuster",
                "🔥 Cyberpunk Neon",
                "☀️ Golden Hour Magic",
                "🌾 Vintage 70s Film",
                "🕶️ Moody Film Noir",
                "👑 Dark Luxury Gold",
                "🚀 Action Thriller Dynamic",
                "🧘 Minimalist Clean Documentary",
                "🖤 High Contrast Monochrome",
                "❄️ Nordic Muted",
                "🎙️ Interview Clean",
                "🎖️ War Documentary",
                "📼 Retro VHS",
                "🌌 IMAX Neutral",
            ],
            index=1,
            help="Select an all-in-one cinematic profile to configure color grading, exposure, vignettes, flares, and transitions in 1-Click!"
        )

        intensity_tier = st.radio(
            "Preset Intensity Tier",
            ["Subtle", "Standard", "Bold"],
            index=1,
            horizontal=True,
            help="Subtle (0.6×), Standard (1.0×), Bold (1.4×) intensity scale across all optical effects."
        )

        pkg_defaults = get_cinematic_package(cinematic_package, intensity_tier=intensity_tier) if cinematic_package != "Custom (Manual Overrides)" else {}

        if cinematic_package != "Custom (Manual Overrides)":
            st.info(f"✨ **{cinematic_package}** ({intensity_tier})  \n*{pkg_defaults.get('description', '')}*")

        master_intensity = st.slider(
            "Master Intensity", 0.50, 1.50, 1.00, 0.05,
            help="Scales the overall preset intensity without changing its color identity."
        )

        adaptive_on = st.checkbox(
            "🎯 Adapt per scene automatically", value=pkg_defaults.get("adaptive", True),
            help="Content-aware: reduces bloom/flares on dark shots without highlights, increases grain in shadows, protects faces."
        )

        with st.expander("⚙️ Advanced Color & VFX Overrides", expanded=(cinematic_package == "Custom (Manual Overrides)")):
            wb_strength = st.slider("Source Normalization (Auto WB)", 0.0, 1.0, float(pkg_defaults.get("wb_strength", 0.70)), 0.05)
            skin_protect = st.slider("Skin Protection Mask", 0.0, 1.0, float(pkg_defaults.get("skin_protect", 0.60)), 0.05)
            rolloff_knee = st.slider("Highlight Rolloff Knee", 0.50, 0.95, float(pkg_defaults.get("rolloff_knee", 0.75)), 0.05)
            saturation   = st.slider("Saturation Push", 0.0, 2.5, float(pkg_defaults.get("saturation", 1.15)), 0.05)
            vignette_strength = st.slider("Vignette Strength", 0.0, 1.0, float(pkg_defaults.get("vignette", 0.25)), 0.05)

            transition_style = st.selectbox(
                "Scene Transition Style",
                [
                    "Seamless Crossfade",
                    "Whip Zoom & Motion Blur",
                    "Glitch RGB Split",
                    "Anamorphic Light Leak",
                    "Clean Cut (Instant)",
                ],
                index=0
            )

            enable_auto_framing = st.checkbox("🎯 AI Auto-Framing (Subject Tracking)", value=True)
            enable_letterbox    = st.checkbox("Cinematic Letterbox Bars", value=pkg_defaults.get("enable_letterbox", True))
            letterbox_ratio     = st.selectbox(
                "Letterbox Ratio",
                ["2.35:1 (Anamorphic)", "2.39:1 (Ultra Scope)", "1.85:1 (Flat)", "4:3 Classic Matte"],
                index=0,
                disabled=not enable_letterbox,
            )

            enable_zoom    = st.checkbox("Ken Burns Zoom Effect", value=pkg_defaults.get("enable_zoom", True))
            zoom_direction = st.selectbox(
                "Zoom Direction",
                ["Slow Zoom In", "Slow Zoom Out", "Random Dynamic"],
                index=0,
                disabled=not enable_zoom,
            )

            enable_transitions = st.checkbox(
                "🔀 Randomized Cinematic Scene Transitions",
                value=True,
                help="Joins scene clips with non-repeating cinematic transitions (Whip Pan, Zoom Blur, RGB Split Glitch, Light Leak Wipe, Speed Ramp)."
            )
            transition_duration = st.slider(
                "Transition Overlap Duration (seconds)",
                0.15, 0.60, 0.35, 0.05,
                disabled=not enable_transitions
            )

            enable_fade   = st.checkbox("Scene Fade Transitions", value=False)
            fade_duration = st.slider("Fade Duration (seconds)", 0.1, 1.0, 0.3, 0.1, disabled=not enable_fade)

            enable_grain    = st.checkbox("Film Grain Effect", value=pkg_defaults.get("enable_grain", False))
            grain_intensity = st.slider("Grain Intensity", 0.0, 1.0, float(pkg_defaults.get("grain_intensity", 0.08)), 0.05, disabled=not enable_grain)

            enable_split_toning     = st.checkbox("Split Toning (Shadow Tint)", value=pkg_defaults.get("enable_split_toning", False))
            split_toning_intensity  = st.slider("Split Toning Intensity", 0.0, 1.0, float(pkg_defaults.get("split_toning_intensity", 0.2)), 0.05, disabled=not enable_split_toning)
            enable_bloom            = st.checkbox("Glow & Bloom Effect", value=pkg_defaults.get("enable_bloom", False))
            bloom_intensity         = st.slider("Bloom Intensity", 0.0, 1.0, float(pkg_defaults.get("bloom_intensity", 0.3)), 0.05, disabled=not enable_bloom)
            enable_anamorphic_flare = st.checkbox("Anamorphic Optical Lens Flare", value=pkg_defaults.get("enable_anamorphic_flare", False))
            enable_chromatic_aberration = st.checkbox("Chromatic Aberration (RGB Split)", value=pkg_defaults.get("enable_chromatic_aberration", False))
            enable_gate_weave       = st.checkbox("Retro Gate Weave (Projector Shake)", value=pkg_defaults.get("enable_gate_weave", False))

        # Build full video_config dictionary
        video_config = dict(pkg_defaults)
        video_config.update({
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "fps": fps_choice,
            "video_duration": video_duration,
            "encoder": encoder_choice,
            "cinematic_package": cinematic_package,
            "master_intensity": master_intensity,
            "adaptive": adaptive_on,
            "wb_strength": wb_strength,
            "skin_protect": skin_protect,
            "rolloff_knee": rolloff_knee,
            "saturation": saturation * master_intensity,
            "vignette": vignette_strength * master_intensity,
            "bloom_intensity": float(bloom_intensity if 'bloom_intensity' in locals() else pkg_defaults.get("bloom_intensity", 0.30)) * master_intensity,
            "grain_intensity": float(grain_intensity if 'grain_intensity' in locals() else pkg_defaults.get("grain_intensity", 0.08)) * master_intensity,
            "transition_style": transition_style,
            "enable_transitions": enable_transitions,
            "transition_duration": transition_duration,
            "enable_auto_framing": enable_auto_framing,
            "enable_letterbox": enable_letterbox,
            "letterbox_ratio": letterbox_ratio,
            "enable_zoom": enable_zoom,
            "zoom_direction": zoom_direction,
            "enable_fade": enable_fade,
            "fade_duration": fade_duration,
            "enable_grain": enable_grain,
            "enable_split_toning": enable_split_toning,
            "split_toning_intensity": split_toning_intensity if 'split_toning_intensity' in locals() else pkg_defaults.get("split_toning_intensity", 0.20),
            "enable_bloom": enable_bloom,
            "enable_anamorphic_flare": enable_anamorphic_flare,
            "enable_chromatic_aberration": enable_chromatic_aberration,
            "enable_gate_weave": enable_gate_weave,
        })


        st.divider()

        # ── 3. SUBTITLE STYLE ────────────────────────────────
        st.header("💬 Subtitle Style")

        st.subheader("📦 Preset Typography Packages")
        subtitle_package = st.selectbox(
            "1-Click Subtitle Package",
            [
                "Custom (Manual Controls)",
                "🔥 Hormozi Kinetic",
                "💥 MrBeast Impact",
                "⚡ Cyberpunk Glitch",
                "✨ Opus Glow",
                "🍿 Cinema Minimalist",
                "🗯️ Comic Boom",
                "📰 News Breaking Ticker",
                "🎤 Karaoke Wave",
                "🔮 Neon Synthwave",
                "⌨️ Typewriter Retro",
            ],
            index=1,
            help="Select a complete industry typography preset or choose Custom for manual tuning."
        )

        sub_style = st.selectbox(
            "Subtitle Visual Style",
            [
                "Kinetic Yellow", "Cyberpunk Neon", "Clean Classic",
                "Boxed Background", "Fire Red", "Instagram White",
                "MrBeast Bold", "Gradient Rainbow", "Minimal Fade",
            ],
            index=0,
            disabled=(subtitle_package != "Custom (Manual Controls)")
        )

        sub_size = st.select_slider(
            "Subtitle Size",
            options=["Tiny", "Small", "Medium", "Large", "Extra Large", "Massive"],
            value="Medium",
        )

        sub_position = st.selectbox(
            "Subtitle Position",
            ["Bottom", "Lower Center", "Center", "Upper Center", "Top"],
            index=0,
        )

        sub_animation = st.selectbox(
            "Word Highlight Animation",
            [
                "Active Word Highlight", "Karaoke Underline", "Scale Pop",
                "All White (No Animation)", "Fade In Words",
            ],
            index=0,
        )

        sub_alignment = st.selectbox(
            "Text Alignment", ["Center", "Left", "Right"], index=0
        )

        font_choice = st.selectbox(
            "Font Family",
            [
                "💥 Impact (Heavy Viral Bold)",
                "🅰️ Arial Black (Modern Bold)",
                "⚡ Trebuchet (Kinetic Dynamic)",
                "📖 Georgia (Cinematic Serif)",
                "🗯️ Comic Sans (Fun & Casual)",
                "🖥️ Courier New (Retro Monospace)",
                "📜 Times New Roman (Classic)",
                "✨ Verdana (Clean Ultra-Readable)",
                "🔹 Tahoma (Crisp Tech)",
                "📱 Segoe UI (Modern UI)",
                "🍿 DejaVu Sans Bold (Default)",
            ],
            index=0,
            help="Select a font family for kinetic subtitles."
        )

        subtitle_language = st.selectbox(
            "Subtitle Text Language",
            [
                "🇬🇧 100% English Subtitles (Default)",
            ],
            index=0,
            help="Extracts audio and translates all voiceovers (Hindi/Hinglish/Foreign) into 100% clean English kinetic subtitles."
        )

        subtitle_bg_box = st.selectbox(
            "Subtitle Background Box",
            [
                "None (Clean Floating Text)",
                "Dark Pill Box",
                "Semi-Transparent Shadow",
            ],
            index=0,
            help="Choose None for clean floating subtitles with outline, or add a dark box."
        )

        stroke_width = st.slider("Text Stroke / Outline Width", 0, 10, 5, 1)

        enable_fact_cards = st.checkbox(
            "📊 Enable AI Fact Cards & Stat Callouts",
            value=True,
            help="Renders animated lower-third info badges when numbers, stats, or facts are mentioned."
        )

        st.divider()


        # ── 5. SOUND DESIGN & BACKGROUND MUSIC ───────────────
        st.header("🎵 Sound Design & Audio")
        st.info("🎤 **Audio Upload Mode**: Your uploaded voiceover audio will be used directly.")

        voice_choice = "en-US-ChristopherNeural"
        voice_speed  = "Normal"

        enable_bg_music = st.checkbox(
            "🎵 AI Background Music & Transition SFX", value=True
        )

        bg_music_mood = st.selectbox(
            "🎵 Background Music Mood",
            [
                "🎬 Cinematic Epic",
                "🔥 Cyberpunk Synthwave",
                "☕ Lo-Fi Chill",
                "📜 Documentary Ambient",
                "🚀 Energetic Action",
                "None",
            ],
            index=0,
            help="Select the musical mood for background track auto-ducking."
        )

        st.divider()


        # ── 6. AI DIRECTOR ───────────────────────────────────
        st.header("🤖 AI Director Settings")

        ai_tone = st.selectbox(
            "Script Tone",
            [
                "Cinematic & Epic", "Documentary", "Motivational",
                "News Style", "Story Narrative", "Educational", "Dramatic",
            ],
            index=0,
        )

        ai_language = st.selectbox(
            "Script Language",
            ["English", "Hindi", "Hinglish", "Spanish", "French", "German", "Arabic"],
            index=0,
        )

        enable_ai_image_fallback = st.checkbox(
            "🎨 AI Image-to-3D Motion Fallback (FLUX 4K)",
            value=True,
            help="Generates photorealistic 4K AI images and converts them to 3D Ken-Burns motion clips when stock videos are unavailable."
        )

    # ── Build video_config ────────────────────────────────────
    scene_count, word_length = DURATION_MAP[video_duration]

    video_config = dict(pkg_defaults)
    video_config.update({
        # Layout
        "aspect_ratio": aspect_ratio,
        "resolution":   resolution,
        "fps":          fps_choice,
        "encoder":      encoder_choice,
        # Color & Cinematic Packages
        "cinematic_package": cinematic_package,
        "color_grade":  pkg_defaults.get("color_grade", "Cinematic Teal & Orange"),
        "brightness":   pkg_defaults.get("brightness", 0),
        "contrast":     pkg_defaults.get("contrast", 1.05),
        "saturation":   saturation * master_intensity,
        "vignette":     vignette_strength * master_intensity,
        "master_intensity": master_intensity,
        "adaptive":     adaptive_on,
        "wb_strength":  wb_strength,
        "skin_protect": skin_protect,
        "rolloff_knee": rolloff_knee,

        # Subtitles
        "subtitle_package": subtitle_package,
        "style":        sub_style,
        "size":         sub_size,
        "position":     sub_position,
        "animation":    sub_animation,
        "alignment":    sub_alignment,
        "font":         font_choice,
        "subtitle_language": subtitle_language,
        "subtitle_bg_box": subtitle_bg_box,
        "stroke_width": stroke_width,
        "enable_fact_cards": enable_fact_cards,

        # VFX
        "enable_auto_framing": enable_auto_framing,
        "transition_style":    transition_style,
        "enable_letterbox":    enable_letterbox,
        "letterbox_ratio":     letterbox_ratio if enable_letterbox else None,
        "enable_zoom":         enable_zoom,
        "zoom_direction":      zoom_direction if enable_zoom else None,
        "enable_fade":         enable_fade,
        "fade_duration":       fade_duration if enable_fade else 0,
        "enable_grain":        enable_grain,
        "grain_intensity":     (grain_intensity * master_intensity) if enable_grain else 0,
        # Pro VFX
        "enable_split_toning":        enable_split_toning,
        "split_toning_intensity":     (split_toning_intensity * master_intensity) if enable_split_toning else 0,
        "enable_bloom":               enable_bloom,
        "bloom_intensity":            (bloom_intensity * master_intensity) if enable_bloom else 0,
        "enable_anamorphic_flare":    enable_anamorphic_flare,
        "enable_chromatic_aberration": enable_chromatic_aberration,
        "enable_gate_weave":           enable_gate_weave,
        # Voice & Audio
        "voice":           voice_choice.split(" (")[0],
        "voice_speed":     voice_speed,
        "enable_bg_music": enable_bg_music,
        "bg_music_mood":   bg_music_mood,
        # AI
        "ai_tone":     ai_tone,
        "ai_language": ai_language,
        "enable_ai_image_fallback": enable_ai_image_fallback,
    })

    return {
        "video_config":    video_config,
        "scene_count":     scene_count,
        "word_length":     word_length,
        "video_duration":  video_duration,
        "ai_tone":         ai_tone,
        "fps_choice":      fps_choice,
        "voice_choice":    voice_choice,
        "aspect_ratio":    aspect_ratio,
        "color_grade":     video_config.get("color_grade", "Cinematic Teal & Orange"),
        "sub_style":       sub_style,
        "audio_mode":      audio_mode,
    }
