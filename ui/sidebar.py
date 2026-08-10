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
        with st.expander("🔤 Typography & Font Family", expanded=(subtitle_package == "Custom (Manual Controls)")):
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
            size_scale = st.slider("Font Scale", 0.5, 2.0, float(sub_pkg_defaults.get("size_scale", 1.0)), 0.05)
            letter_spacing = st.slider("Letter Spacing (px)", 0, 10, int(sub_pkg_defaults.get("letter_spacing", 0)), 1)
            word_spacing = st.slider("Word Spacing (px)", 0, 30, int(sub_pkg_defaults.get("word_spacing", 10)), 1)

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
        st.header("🎬 Intro / Outro / Cards")

        with st.expander("🎬 Intro Title Card", expanded=False):
            show_intro = st.checkbox("Enable Intro Card", value=True)
            intro_duration = st.slider("Intro Duration (sec)", 2.0, 6.0, 3.0, 0.5)
            intro_style_override = st.selectbox(
                "Animation Style",
                ["AI Auto-Pick", "Particle Assemble", "Glow Reveal", "Cinematic Scale", "Typewriter"],
                index=0
            )
            intro_bg_style = st.selectbox(
                "Background",
                ["Solid Black", "Gradient Dark", "Radial Glow"],
                index=2
            )
            intro_title_color = st.color_picker("Title Color", "#FFFFFF")
            intro_glow_color = st.color_picker("Glow Color", "#4488FF")
            intro_glow_radius = st.slider("Glow Intensity", 0, 30, 15)
            intro_letter_spacing = st.slider("Letter Spacing", 0, 20, 8)
            intro_show_subtitle = st.checkbox("Show Subtitle Tagline", True)
            intro_subtitle_color = st.color_picker("Subtitle Color", "#9999CC")

        with st.expander("📖 Chapter Title Cards", expanded=False):
            show_chapters = st.checkbox("Enable Chapter Cards", value=True)
            chapter_style = st.selectbox(
                "Animation",
                ["Slide Horizontal", "Slide Vertical", "Fade", "Wipe"],
                index=0
            )
            chapter_position = st.selectbox(
                "Position",
                ["Center", "Lower Third", "Upper Third"],
                index=0
            )
            chapter_bg_color = st.color_picker("Card Background", "#000000")
            chapter_bg_opacity = st.slider("Card Opacity", 0, 255, 180)
            chapter_text_color = st.color_picker("Text Color", "#FFFFFF")
            chapter_accent_color = st.color_picker("Accent / Line Color", "#4488FF")
            chapter_show_lines = st.checkbox("Show Decorative Lines", True)

        with st.expander("🎬 Outro Card", expanded=False):
            show_outro = st.checkbox("Enable Outro Card", value=True)
            outro_duration = st.slider("Outro Duration (sec)", 2.0, 6.0, 4.0, 0.5)
            outro_channel_name = st.text_input("Channel Name", "@YourChannel")
            outro_cta_override = st.text_input("CTA Text Override (blank = AI picks)", "")
            outro_show_subscribe = st.checkbox("Show Subscribe Button", True)
            outro_show_like = st.checkbox("Show Like & Share", True)
            outro_accent_color = st.color_picker("Accent Color", "#FF0000")
            outro_bg_style = st.selectbox(
                "Background", ["Solid Black", "Gradient Dark"], index=0
            )

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
        "active_color":     active_rgb if subtitle_package == "Custom (Manual Controls)" else sub_pkg_defaults.get("active_color", active_rgb),
        "inactive_color":   inactive_rgb if subtitle_package == "Custom (Manual Controls)" else sub_pkg_defaults.get("inactive_color", inactive_rgb),
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

        # Intro Card Settings
        "show_intro": show_intro,
        "intro_duration": intro_duration,
        "intro_style_override": None if intro_style_override == "AI Auto-Pick" else intro_style_override.lower().replace(" ", "_"),
        "intro_bg_style": intro_bg_style.lower().replace(" ", "_"),
        "intro_title_color": hex_to_rgb_tuple(intro_title_color),
        "intro_glow_color": hex_to_rgb_tuple(intro_glow_color),
        "intro_glow_radius": intro_glow_radius,
        "intro_letter_spacing": intro_letter_spacing,
        "intro_show_subtitle": intro_show_subtitle,
        "intro_subtitle_color": hex_to_rgb_tuple(intro_subtitle_color),

        # Chapter Title Cards Settings
        "show_chapter_cards": show_chapters,
        "chapter_card_style": chapter_style.lower().replace(" ", "_"),
        "chapter_card_position": chapter_position.lower().replace(" ", "_"),
        "chapter_card_bg_color": hex_to_rgb_tuple(chapter_bg_color) + (chapter_bg_opacity,),
        "chapter_card_text_color": hex_to_rgb_tuple(chapter_text_color),
        "chapter_card_accent_color": hex_to_rgb_tuple(chapter_accent_color),
        "chapter_card_show_lines": chapter_show_lines,

        # Outro Card Settings
        "show_outro": show_outro,
        "outro_duration": outro_duration,
        "outro_channel_name": outro_channel_name,
        "outro_cta_override": outro_cta_override if outro_cta_override else None,
        "outro_show_subscribe": outro_show_subscribe,
        "outro_show_like": outro_show_like,
        "outro_accent_color": hex_to_rgb_tuple(outro_accent_color),
        "outro_bg_style": outro_bg_style.lower().replace(" ", "_"),
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
