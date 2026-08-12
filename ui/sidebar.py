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
from modules.subtitle_packages import get_subtitle_package, SUBTITLE_PACKAGES

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
    audio_mode = "🎤 Upload Your Own Audio"

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
            help="CPU works on every machine. NVENC/QuickSync are 5-10× faster but require NVIDIA/Intel GPU drivers."
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
        )

        intensity_tier = st.radio(
            "Preset Intensity Tier",
            ["Subtle", "Standard", "Bold"],
            index=1,
            horizontal=True,
        )

        pkg_defaults = get_cinematic_package(cinematic_package, intensity_tier=intensity_tier) if cinematic_package != "Custom (Manual Overrides)" else {}

        if cinematic_package != "Custom (Manual Overrides)":
            st.info(f"✨ **{cinematic_package}** ({intensity_tier})  \n*{pkg_defaults.get('description', '')}*")

        master_intensity = st.slider("Master Intensity", 0.50, 1.50, 1.00, 0.05)
        adaptive_on = st.checkbox("🎯 Adapt per scene automatically", value=pkg_defaults.get("adaptive", True))

        with st.expander("⚙️ Advanced Color & VFX Overrides", expanded=(cinematic_package == "Custom (Manual Overrides)")):
            wb_strength = st.slider("Source Normalization (Auto WB)", 0.0, 1.0, float(pkg_defaults.get("wb_strength", 0.70)), 0.05)
            skin_protect = st.slider("Skin Protection Mask", 0.0, 1.0, float(pkg_defaults.get("skin_protect", 0.60)), 0.05)
            rolloff_knee = st.slider("Highlight Rolloff Knee", 0.50, 0.95, float(pkg_defaults.get("rolloff_knee", 0.75)), 0.05)
            saturation   = st.slider("Saturation Push", 0.0, 2.5, float(pkg_defaults.get("saturation", 1.15)), 0.05)
            vignette_strength = st.slider("Vignette Strength", 0.0, 1.0, float(pkg_defaults.get("vignette", 0.25)), 0.05)

            transition_style = st.selectbox(
                "Scene Transition Style",
                ["Seamless Crossfade", "Whip Zoom & Motion Blur", "Glitch RGB Split", "Anamorphic Light Leak", "Clean Cut (Instant)"],
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

            enable_transitions = st.checkbox("🔀 Randomized Cinematic Scene Transitions", value=True)
            transition_duration = st.slider("Transition Overlap Duration (seconds)", 0.15, 0.60, 0.35, 0.05, disabled=not enable_transitions)
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

        st.divider()

        # ── 3. SUBTITLE ENGINE CONTROLS (EXPANDERS) ──────────
        st.header("💬 Professional Subtitle Engine")

        subtitle_package = st.selectbox(
            "📦 Typography Package (Preset)",
            list(SUBTITLE_PACKAGES.keys()) + ["Custom (Manual Controls)"],
            index=0,
            help="Select a industry typography preset or customize every detail manually below!"
        )

        sub_pkg_defaults = get_subtitle_package(subtitle_package) if subtitle_package != "Custom (Manual Controls)" else {}

        # ── EXPANDER 1: TYPOGRAPHY & FONT ──
        with st.expander("🔤 Typography & Font Family", expanded=True):
            font_choice = st.selectbox(
                "Font Family",
                [
                    "🍿 DejaVu Sans Bold (Default)",
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
                ],
                index=0,
            )
            st.markdown("**Text Size & Spacing Controls**")
            size_preset = st.radio(
                "Quick Text Size Presets",
                ["🔍 Small (0.8x)", "💬 Normal (1.2x)", "🔥 Large (1.6x)", "💥 Extra Large (2.2x)", "🚀 Giant (3.5x)", "Custom Slider"],
                index=5,
                horizontal=True,
            )
            preset_scale_map = {
                "🔍 Small (0.8x)": 0.80,
                "💬 Normal (1.2x)": 1.20,
                "🔥 Large (1.6x)": 1.60,
                "💥 Extra Large (2.2x)": 2.20,
                "🚀 Giant (3.5x)": 3.50,
            }
            default_scale = preset_scale_map.get(size_preset, float(sub_pkg_defaults.get("size_scale", 1.40)))

            size_scale = st.slider(
                "Font Scale (Text Size)",
                0.30, 4.00, default_scale, 0.05,
                help="Adjust subtitle text size from micro (0.3x) to giant (4.0x)!"
            )
            letter_spacing = st.slider("Letter Spacing (px)", 0, 15, int(sub_pkg_defaults.get("letter_spacing", 0)), 1)
            word_spacing = st.slider("Word Spacing (px)", 0, 40, int(sub_pkg_defaults.get("word_spacing", 10)), 1)
            max_width_pct = st.slider("Text Max Screen Width (%)", 40, 100, 85, 5, help="Controls horizontal wrapping boundary for text")

        # ── EXPANDER 2: POSITIONING & LAYOUT ──
        with st.expander("📍 Positioning & Text Layout", expanded=False):
            sub_position = st.selectbox(
                "Subtitle Screen Position",
                ["Bottom", "Lower Third", "Center", "Upper Third", "Top", "Custom"],
                index=["Bottom", "Lower Third", "Center", "Upper Third", "Top", "Custom"].index(sub_pkg_defaults.get("position", "Bottom")) if sub_pkg_defaults.get("position") in ["Bottom", "Lower Third", "Center", "Upper Third", "Top", "Custom"] else 0
            )
            custom_y_pct = st.slider("Custom Y% (0=Top, 100=Bottom)", 0, 100, int(sub_pkg_defaults.get("custom_y_pct", 85)), 1)
            
            layout_mode = st.selectbox(
                "Text Layout Mode",
                ["Single Line", "Two Lines", "Word-by-Word", "Three Words at a Time", "Full Sentence"],
                index=["Single Line", "Two Lines", "Word-by-Word", "Three Words at a Time", "Full Sentence"].index(sub_pkg_defaults.get("layout_mode", "Two Lines")) if sub_pkg_defaults.get("layout_mode") in ["Single Line", "Two Lines", "Word-by-Word", "Three Words at a Time", "Full Sentence"] else 1
            )

        # ── EXPANDER 3: ANIMATIONS ──
        with st.expander("✨ Word Highlight Animation", expanded=False):
            animation_type = st.selectbox(
                "Active Word Animation",
                ["scale_pop", "bounce", "shake", "glow", "karaoke_fill", "typewriter", "fade_in_word", "tilt", "none"],
                index=["scale_pop", "bounce", "shake", "glow", "karaoke_fill", "typewriter", "fade_in_word", "tilt", "none"].index(sub_pkg_defaults.get("animation_type", "scale_pop")) if sub_pkg_defaults.get("animation_type") in ["scale_pop", "bounce", "shake", "glow", "karaoke_fill", "typewriter", "fade_in_word", "tilt", "none"] else 0
            )
            enable_emojis = st.checkbox("🔥 Auto-Emoji Highlights", value=sub_pkg_defaults.get("enable_emojis", True))

        # ── EXPANDER 4: BACKGROUND / BOX STYLES ──
        with st.expander("📦 Background & Box Styles", expanded=False):
            background_type = st.selectbox(
                "Background Style",
                ["none", "full_width_bar", "pill", "word_box", "shadow_only", "gradient_bar"],
                index=["none", "full_width_bar", "pill", "word_box", "shadow_only", "gradient_bar"].index(sub_pkg_defaults.get("background_type", "none")) if sub_pkg_defaults.get("background_type") in ["none", "full_width_bar", "pill", "word_box", "shadow_only", "gradient_bar"] else 0
            )
            bg_color_hex = st.color_picker("Box Fill Color", "#000000")
            bg_opacity = st.slider("Box Opacity (%)", 0, 100, 70, 5)

        # ── EXPANDER 5: STROKE & OUTLINE ──
        with st.expander("🖊️ Stroke & Outline", expanded=False):
            stroke_style = st.selectbox(
                "Stroke Style",
                ["solid", "double", "glitch", "none"],
                index=["solid", "double", "glitch", "none"].index(sub_pkg_defaults.get("stroke_style", "solid")) if sub_pkg_defaults.get("stroke_style") in ["solid", "double", "glitch", "none"] else 0
            )
            stroke_width = st.slider("Stroke Width (px)", 0, 10, int(sub_pkg_defaults.get("stroke_width", 5)), 1)
            stroke_color_hex = st.color_picker("Stroke Color", "#000000")

        # ── EXPANDER 6: SHADOW & NEON GLOW ──
        with st.expander("🌟 Shadow & Neon Glow", expanded=False):
            st.markdown("**Drop Shadow**")
            enable_shadow = st.checkbox("Enable Drop Shadow", value=sub_pkg_defaults.get("shadow") is not None)
            shadow_offset_x = st.slider("Shadow Offset X", -10, 10, 4, 1)
            shadow_offset_y = st.slider("Shadow Offset Y", -10, 10, 4, 1)
            shadow_color_hex = st.color_picker("Shadow Color", "#000000")
            shadow_opacity = st.slider("Shadow Opacity", 0.0, 1.0, 0.8, 0.05)

            st.divider()
            st.markdown("**Neon Glow & Bloom**")
            enable_glow = st.checkbox("Enable Neon Glow", value=sub_pkg_defaults.get("glow") is not None)
            glow_color_hex = st.color_picker("Glow Color", "#00FFFF")
            glow_radius = st.slider("Glow Radius", 1, 20, 10, 1)
            glow_opacity = st.slider("Glow Opacity", 0.0, 1.0, 0.8, 0.05)

        # ── EXPANDER 7: COLOR CONTROLS ──
        with st.expander("🎨 Word Colors (Active & Inactive)", expanded=False):
            active_color_hex = st.color_picker("Active Word Color", "#FFEB3B")
            inactive_color_hex = st.color_picker("Inactive Word Color", "#FFFFFF")

        # ── EXPANDER 8: FACT TEXT OVERLAY (NO-BOX TEXT) ──
        with st.expander("📊 Fact Text Overlay (No-Box Styled Text)", expanded=False):
            enable_fact_text_overlay = st.checkbox("Enable Fact Text Overlay", value=True)
            fact_font_family = st.selectbox(
                "Fact Font Family",
                [
                    "🍿 DejaVu Sans Bold (Default)",
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
                ],
                index=0,
            )
            col_fs1, col_fs2 = st.columns(2)
            with col_fs1:
                fact_font_scale = st.slider("Fact Font Scale", 0.5, 2.5, 1.0, 0.1)
                fact_fill_style = st.selectbox("Fill Style", ["solid", "gradient"], index=0)
            with col_fs2:
                if fact_fill_style == "solid":
                    fact_color_hex = st.color_picker("Fact Text Color", "#FFFFFF")
                    fact_grad1_hex = "#FFD700"
                    fact_grad2_hex = "#FF7828"
                else:
                    fact_color_hex = "#FFFFFF"
                    fact_grad1_hex = st.color_picker("Gradient Stop 1", "#FFD700")
                    fact_grad2_hex = st.color_picker("Gradient Stop 2", "#FF7828")

            col_fp1, col_fp2 = st.columns(2)
            with col_fp1:
                fact_position = st.selectbox("Position", ["Bottom", "Top", "Center", "Custom"], index=0)
            with col_fp2:
                fact_custom_y_percent = st.slider("Custom Y Offset (%)", 0.0, 100.0, 80.0, 1.0) if fact_position == "Custom" else 80.0

            col_ft1, col_ft2 = st.columns(2)
            with col_ft1:
                fact_start_tracking = st.slider("Start Tracking (px)", 10, 60, 30, 2)
            with col_ft2:
                fact_end_tracking = st.slider("End Tracking (px)", 0, 20, 6, 1)

            col_fa1, col_fa2 = st.columns(2)
            with col_fa1:
                fact_entrance_animation = st.selectbox("Entrance Animation", ["tracking", "fade", "slide_up", "slide_down", "word_reveal"], index=0)
            with col_fa2:
                fact_exit_animation = st.selectbox("Exit Animation", ["fade", "slide_up", "slide_down", "none"], index=0)

            col_leg1, col_leg2 = st.columns(2)
            with col_leg1:
                fact_outline_width = st.slider("Outline Width (px)", 2, 8, 3, 1)
            with col_leg2:
                fact_shadow_opacity = st.slider("Shadow Opacity", 0.3, 1.0, 0.6, 0.05)

            fact_display_duration = st.slider("Display Duration (sec)", 1.0, 6.0, 2.5, 0.5)

        enable_fact_cards = st.checkbox("📊 Enable AI Fact Cards & Stat Callouts", value=True)

        st.divider()

        # ── 4. AI DIRECTOR ───────────────────────────────────
        st.header("🤖 AI Director Settings")
        ai_tone = st.selectbox(
            "Script Tone",
            ["Cinematic & Epic", "Documentary", "Motivational", "News Style", "Story Narrative", "Educational", "Dramatic"],
            index=0,
        )
        ai_language = st.selectbox(
            "Script Language",
            ["English", "Hindi", "Hinglish", "Spanish", "French", "German", "Arabic"],
            index=0,
        )
        enable_ai_image_fallback = st.checkbox("🎨 AI Image Fallback", value=True)

        st.divider()

        # ── 5. INTRO / OUTRO / CARDS ─────────────────────────
        st.header("🎬 Intro / Outro / Cards (Full Typography Control)")

        overlay_preset_choice = st.selectbox(
            "🎨 Master Title Theme Preset",
            ["🎬 Cinematic Warm", "🔮 Neon Synthwave", "💥 MrBeast Energy", "🍿 Cinema Minimalist", "Custom (Per-Card Overrides)"],
            index=0,
            help="Applies a unified typography, color, and animation language across Intro, Chapter, and Outro cards together!"
        )

        auto_color_from_video = st.checkbox("🎯 Auto-Extract Color from Video Frame", value=False, help="Dynamically samples dominant color from video clips to auto-style accent colors!")

        card_font_family = st.selectbox(
            "🔤 Title Cards Font Family",
            [
                "🍿 DejaVu Sans Bold (Default)",
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
            ],
            index=0,
        )

        with st.expander("🎬 Intro Title Card Settings", expanded=False):
            show_intro = st.checkbox("Enable Intro Card", value=True)
            intro_duration = st.slider("Intro Duration (sec)", 2.0, 6.0, 4.0, 0.5)
            intro_style_override = st.selectbox(
                "Animation Style",
                ["AI Auto-Pick", "Blur to Sharp", "Neon Trace", "Split Reveal", "Glow Reveal", "Particle Assemble", "Cinematic Scale", "Typewriter"],
                index=0
            )
            intro_position = st.selectbox(
                "Intro Screen Position",
                ["Center", "Upper Third", "Lower Third"],
                index=0
            )
            col_is1, col_is2 = st.columns(2)
            with col_is1:
                intro_title_size_scale = st.slider("Intro Font Scale", 0.30, 4.00, 1.20, 0.05, help="Scales main title text size from micro (0.3x) to giant (4.0x)")
                intro_word_spacing = st.slider("Intro Word Spacing (px)", 0, 50, 10, 1)
            with col_is2:
                intro_line_gap = st.slider("Title / Subtitle Gap (px)", 0, 50, 16, 2)
                intro_start_tracking = st.slider("Start Tracking (px)", 10, 60, 24, 2, help="Letters start wide apart on reveal")
                intro_end_tracking = st.slider("End Tracking (px)", 0, 30, 6, 1, help="Letters compress inward to settled spacing")

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                grad_stop1 = st.color_picker("Text Gradient Stop 1", "#FFD700")
            with col_g2:
                grad_stop2 = st.color_picker("Text Gradient Stop 2", "#FF7828")

            intro_glow_color = st.color_picker("Glow Color", "#FF8C00")
            intro_glow_radius = st.slider("Glow Intensity", 0, 30, 18)
            intro_show_subtitle = st.checkbox("Show Subtitle Tagline", True)
            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                intro_subtitle_size_scale = st.slider("Subtitle Font Scale", 0.30, 4.00, 1.20, 0.05, help="Increase or decrease tagline font size (0.3x to 4.0x)")
                intro_subtitle_color = st.color_picker("Subtitle Color", "#9999CC")
            with col_sub2:
                intro_subtitle_letter_spacing = st.slider("Subtitle Tracking (px)", 0, 30, 2, 1)

        with st.expander("📖 Chapter Title Cards Settings", expanded=False):
            show_chapters = st.checkbox("Enable Chapter Cards", value=True)
            chapter_style = st.selectbox(
                "Animation",
                [
                    "Bracket Frame",
                    "Underline Draw",
                    "Slide Horizontal",
                    "Slide Vertical",
                    "Fade",
                    "Wipe",
                    "Blur to Sharp",
                    "Glow Pulse Border",
                    "Holographic HUD Scan",
                    "Split Center Zoom",
                    "Kinetic Bounce Pop",
                    "Neon Outline Trace",
                ],
                index=0
            )
            chapter_position = st.selectbox(
                "Position",
                ["Center", "Lower Third", "Upper Third"],
                index=0
            )
            col_cs1, col_cs2 = st.columns(2)
            with col_cs1:
                chapter_font_scale = st.slider("Chapter Font Scale", 0.30, 4.00, 1.20, 0.05, help="Increase or decrease chapter font size")
                chapter_word_spacing = st.slider("Chapter Word Spacing (px)", 0, 50, 10, 1)
            with col_cs2:
                chapter_letter_spacing = st.slider("Chapter Letter Spacing (px)", 0, 30, 4, 1)
            chapter_bg_color = st.color_picker("Card Background", "#0F172A")
            chapter_bg_opacity = st.slider("Card Opacity", 0, 255, 200)
            chapter_text_color = st.color_picker("Text Color", "#FFFFFF")
            chapter_accent_color = st.color_picker("Accent / Line Color", "#FFA028")
            chapter_show_lines = st.checkbox("Show Decorative Lines", True)

        with st.expander("🎬 Outro Card Settings", expanded=False):
            show_outro = st.checkbox("Enable Outro Card", value=True)
            outro_duration = st.slider("Outro Duration (sec)", 2.0, 6.0, 4.0, 0.5)
            outro_style_override = st.selectbox(
                "Animation Style",
                ["AI Auto-Pick", "Blur to Sharp", "Neon Trace", "Split Reveal", "Glow Reveal", "Particle Assemble", "Cinematic Scale", "Typewriter"],
                index=0,
                key="outro_style_sel"
            )
            outro_position = st.selectbox(
                "Outro Screen Position",
                ["Center", "Upper Third", "Lower Third"],
                index=0
            )
            outro_heading_override = st.text_input("Main Heading Text (blank = THANKS FOR WATCHING!)", "", help="Type any custom heading text to show on Outro card instead of default THANKS FOR WATCHING!")
            outro_cta_override = st.text_input("CTA Subtitle Text (blank = AI picks)", "", help="Type custom call-to-action tagline (e.g., LIKE & SUBSCRIBE FOR MORE)")
            outro_channel_name = st.text_input("Channel Name / Handle", "@YourChannel")

            st.markdown("###### 📏 Independent Section Text Size Controls")
            col_os1, col_os2 = st.columns(2)
            with col_os1:
                outro_font_scale = st.slider("Top Heading Scale", 0.30, 4.00, 1.10, 0.05, help="Increase or decrease Top Heading text size")
                outro_btn_scale = st.slider("Subscribe Button Scale", 0.30, 3.00, 1.00, 0.05, help="Increase or decrease Subscribe button size")
                outro_channel_scale = st.slider("Channel Handle Scale", 0.30, 3.00, 1.00, 0.05, help="Increase or decrease Channel Handle size")
                outro_word_spacing = st.slider("Outro Word Spacing (px)", 0, 50, 10, 1)
            with col_os2:
                outro_cta_scale = st.slider("Middle Subtitle Scale", 0.30, 3.00, 0.85, 0.05, help="Increase or decrease Middle Subtitle text size")
                outro_badges_scale = st.slider("Bottom Badges Scale", 0.30, 3.00, 1.00, 0.05, help="Increase or decrease Bottom Badges text size")
                outro_line_gap = st.slider("Heading / CTA Gap (px)", 0, 50, 16, 2)

            outro_start_tracking = st.slider("Start Tracking (px)", 10, 60, 24, 2, help="Letters start wide apart on reveal", key="outro_start_track")
            outro_end_tracking = st.slider("End Tracking (px)", 0, 30, 6, 1, help="Letters compress inward to settled spacing", key="outro_end_track")

            col_og1, col_og2 = st.columns(2)
            with col_og1:
                outro_grad_stop1 = st.color_picker("Text Gradient Stop 1", "#FFD700", key="outro_g1")
            with col_og2:
                outro_grad_stop2 = st.color_picker("Text Gradient Stop 2", "#FF7828", key="outro_g2")

            outro_glow_color = st.color_picker("Glow Color", "#FF8C00", key="outro_glow_c")
            outro_glow_radius = st.slider("Glow Intensity", 0, 30, 18, key="outro_glow_r")

            outro_show_subscribe = st.checkbox("Show Subscribe Button", True)
            outro_show_like = st.checkbox("Show Like & Share", True)
            outro_accent_color = st.color_picker("Accent Color", "#FF7828")

    # ── Convert Hex Colors to RGBA/RGB ──
    def hex_to_rgb_tuple(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    bg_rgb = hex_to_rgb_tuple(bg_color_hex)
    bg_rgba = (bg_rgb[0], bg_rgb[1], bg_rgb[2], int(255 * (bg_opacity / 100.0)))
    active_rgb = hex_to_rgb_tuple(active_color_hex)
    inactive_rgb = hex_to_rgb_tuple(inactive_color_hex)
    stroke_rgb = hex_to_rgb_tuple(stroke_color_hex)
    shadow_rgb = hex_to_rgb_tuple(shadow_color_hex)
    glow_rgb = hex_to_rgb_tuple(glow_color_hex)

    # Build video_config dictionary
    scene_count, word_length = DURATION_MAP[video_duration]

    video_config = dict(pkg_defaults)
    video_config.update({
        "aspect_ratio": aspect_ratio,
        "resolution":   resolution,
        "fps":          fps_choice,
        "encoder":      encoder_choice,
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

        # Subtitle Engine Settings
        "subtitle_package": subtitle_package,
        "font_file":        font_choice.split(" (")[0].strip(),
        "font":             font_choice,
        "size_scale":       size_scale,
        "letter_spacing":   letter_spacing,
        "word_spacing":     word_spacing,
        "max_width_pct":   max_width_pct,
        "position":         sub_position,
        "custom_y_pct":     custom_y_pct,
        "layout_mode":      layout_mode,
        "animation_type":   animation_type,
        "enable_emojis":    enable_emojis,
        "background_type":  background_type,
        "bg_color":         bg_rgba,
        "stroke_style":     stroke_style,
        "stroke_width":     stroke_width,
        "stroke_color":     stroke_rgb,
        "active_color":     active_rgb,
        "inactive_color":   inactive_rgb,
        "shadow": {
            "offset_x": shadow_offset_x,
            "offset_y": shadow_offset_y,
            "color": shadow_rgb,
            "opacity": shadow_opacity,
            "blur": 2,
        } if enable_shadow else None,
        "glow": {
            "color": glow_rgb,
            "radius": glow_radius,
            "opacity": glow_opacity,
        } if enable_glow else None,

        # Fact Text Overlay Settings
        "enable_fact_text_overlay": enable_fact_text_overlay,
        "enable_fact_cards": enable_fact_cards,
        "fact_font_family": fact_font_family,
        "fact_font_scale": fact_font_scale,
        "fact_fill_style": fact_fill_style,
        "fact_color": hex_to_rgb_tuple(fact_color_hex),
        "fact_gradient": (hex_to_rgb_tuple(fact_grad1_hex), hex_to_rgb_tuple(fact_grad2_hex)),
        "fact_position": fact_position,
        "fact_custom_y_pct": fact_custom_y_percent,
        "start_tracking": fact_start_tracking,
        "end_tracking": fact_end_tracking,
        "entrance_animation": fact_entrance_animation,
        "exit_animation": fact_exit_animation,
        "outline_width": fact_outline_width,

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
        "enable_split_toning": enable_split_toning,
        "split_toning_intensity": (split_toning_intensity * master_intensity) if enable_split_toning else 0,
        "enable_bloom":        enable_bloom,
        "bloom_intensity":     (bloom_intensity * master_intensity) if enable_bloom else 0,
        "enable_anamorphic_flare": enable_anamorphic_flare,
        "enable_chromatic_aberration": enable_chromatic_aberration,
        "enable_gate_weave":   enable_gate_weave,

        # Audio & AI
        "voice":           "en-US-ChristopherNeural",
        "voice_speed":     "Normal",
        "enable_bg_music": False,
        "bg_music_mood":   "None",
        "ai_tone":         ai_tone,
        "ai_language":     ai_language,
        "enable_ai_image_fallback": enable_ai_image_fallback,

        # Title Cards & Motion Graphics Settings
        "overlay_preset": overlay_preset_choice,
        "auto_color_from_video": auto_color_from_video,
        "card_font_family": card_font_family,

        # Intro Card Settings
        "show_intro": show_intro,
        "intro_duration": intro_duration,
        "intro_style_override": None if intro_style_override == "AI Auto-Pick" else intro_style_override.lower().replace(" ", "_"),
        "intro_position": intro_position,
        "intro_title_size_scale": intro_title_size_scale,
        "intro_word_spacing": intro_word_spacing,
        "intro_line_gap": intro_line_gap,
        "intro_start_tracking": intro_start_tracking,
        "intro_end_tracking": intro_end_tracking,
        "gradient_colors": (hex_to_rgb_tuple(grad_stop1), hex_to_rgb_tuple(grad_stop2)),
        "intro_glow_color": hex_to_rgb_tuple(intro_glow_color),
        "intro_glow_radius": intro_glow_radius,
        "intro_show_subtitle": intro_show_subtitle,
        "intro_subtitle_color": hex_to_rgb_tuple(intro_subtitle_color),
        "intro_subtitle_size_scale": intro_subtitle_size_scale,
        "intro_subtitle_letter_spacing": intro_subtitle_letter_spacing,

        # Chapter Title Cards Settings
        "show_chapter_cards": show_chapters,
        "chapter_card_style": chapter_style.lower().replace(" ", "_"),
        "chapter_card_position": chapter_position.lower().replace(" ", "_"),
        "chapter_font_scale": chapter_font_scale,
        "chapter_word_spacing": chapter_word_spacing,
        "chapter_letter_spacing": chapter_letter_spacing,
        "chapter_card_bg_color": hex_to_rgb_tuple(chapter_bg_color) + (chapter_bg_opacity,),
        "chapter_card_text_color": hex_to_rgb_tuple(chapter_text_color),
        "chapter_card_accent_color": hex_to_rgb_tuple(chapter_accent_color),
        "chapter_card_show_lines": chapter_show_lines,

        # Outro Card Settings
        "show_outro": show_outro,
        "outro_duration": outro_duration,
        "outro_style_override": None if outro_style_override == "AI Auto-Pick" else outro_style_override.lower().replace(" ", "_"),
        "outro_position": outro_position,
        "outro_thanks_text": outro_heading_override if outro_heading_override else None,
        "outro_font_scale": outro_font_scale,
        "outro_cta_scale": outro_cta_scale,
        "outro_btn_scale": outro_btn_scale,
        "outro_badges_scale": outro_badges_scale,
        "outro_channel_scale": outro_channel_scale,
        "outro_word_spacing": outro_word_spacing,
        "outro_line_gap": outro_line_gap,
        "outro_start_tracking": outro_start_tracking,
        "outro_end_tracking": outro_end_tracking,
        "outro_gradient_colors": (hex_to_rgb_tuple(outro_grad_stop1), hex_to_rgb_tuple(outro_grad_stop2)),
        "outro_glow_color": hex_to_rgb_tuple(outro_glow_color),
        "outro_glow_radius": outro_glow_radius,
        "outro_channel_name": outro_channel_name,
        "outro_cta_override": outro_cta_override if outro_cta_override else None,
        "outro_show_subscribe": outro_show_subscribe,
        "outro_show_like": outro_show_like,
        "outro_accent_color": hex_to_rgb_tuple(outro_accent_color),
    })

    return {
        "video_config":    video_config,
        "scene_count":     scene_count,
        "word_length":     word_length,
        "video_duration":  video_duration,
        "ai_tone":         ai_tone,
        "fps_choice":      fps_choice,
        "aspect_ratio":    aspect_ratio,
        "color_grade":     video_config.get("color_grade", "Cinematic Teal & Orange"),
        "sub_style":       subtitle_package,
        "audio_mode":      audio_mode,
    }
