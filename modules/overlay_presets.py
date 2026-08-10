"""
modules/overlay_presets.py
─────────────────────────────────────────────────────────────────────────────
Unified Theme Presets for Title Cards & Motion Graphics in Pixelab.

Bundles font, spacing, gradient colors, glow, and animation styles into
cohesive named presets that style Intro, Chapter, and Outro cards together:
  1. 🎬 Cinematic Warm   — Deep amber gradient, tracking compression, blur-to-sharp
  2. 🔮 Neon Synthwave   — Hot pink/cyan gradient, outer neon glow, neon trace
  3. 💥 MrBeast Energy   — Heavy viral bold, spring bounce, underline draw
  4. 🍿 Cinema Minimalist — Crisp clean serif, tracking compress, bracket frame
─────────────────────────────────────────────────────────────────────────────
"""

OVERLAY_PRESETS = {
    "🎬 Cinematic Warm": {
        "description": "Deep amber gradient, tracking compression, blur-to-sharp reveal & vignette depth",
        "font": "📖 Georgia (Cinematic Serif)",
        "intro_animation": "blur_to_sharp",
        "chapter_animation": "bracket_frame",
        "outro_animation": "gradient_pulse_border",
        "intro_start_tracking": 36,
        "intro_end_tracking": 8,
        "fill_style": "gradient",
        "gradient_colors": ((255, 215, 0), (255, 120, 40)),
        "gradient_angle": 45,
        "glow": True,
        "intro_glow_color": (255, 140, 0),
        "intro_glow_radius": 18,
        "bg_depth_treatment": "vignette_patch",
        "chapter_card_position": "center",
        "chapter_card_bg_color": (15, 23, 42, 200),
        "chapter_card_accent_color": (255, 160, 40),
        "outro_accent_color": (255, 120, 40),
    },

    "🔮 Neon Synthwave": {
        "description": "Hot pink/cyan gradient, outer neon glow, neon trace & gradient pulse border",
        "font": "💥 Impact (Heavy Viral Bold)",
        "intro_animation": "neon_trace",
        "chapter_animation": "underline_draw",
        "outro_animation": "gradient_pulse_border",
        "intro_start_tracking": 40,
        "intro_end_tracking": 10,
        "fill_style": "gradient",
        "gradient_colors": ((255, 0, 180), (0, 255, 240)),
        "gradient_angle": 90,
        "glow": True,
        "intro_glow_color": (0, 255, 240),
        "intro_glow_radius": 22,
        "bg_depth_treatment": "glow_blob",
        "chapter_card_position": "center",
        "chapter_card_bg_color": (10, 10, 30, 210),
        "chapter_card_accent_color": (0, 255, 240),
        "outro_accent_color": (255, 0, 180),
    },

    "💥 MrBeast Energy": {
        "description": "Heavy viral bold, spring pop scale, underline draw & vibrant yellow CTA",
        "font": "💥 Impact (Heavy Viral Bold)",
        "intro_animation": "split_reveal",
        "chapter_animation": "underline_draw",
        "outro_animation": "gradient_pulse_border",
        "intro_start_tracking": 20,
        "intro_end_tracking": 4,
        "fill_style": "gradient",
        "gradient_colors": ((255, 235, 59), (255, 87, 34)),
        "gradient_angle": 0,
        "glow": True,
        "intro_glow_color": (255, 235, 59),
        "intro_glow_radius": 14,
        "bg_depth_treatment": "vignette_patch",
        "chapter_card_position": "lower_third",
        "chapter_card_bg_color": (0, 0, 0, 220),
        "chapter_card_accent_color": (255, 235, 59),
        "outro_accent_color": (255, 235, 59),
    },

    "🍿 Cinema Minimalist": {
        "description": "Crisp clean serif, tracking compression, bracket frame & minimal vignette depth",
        "font": "📖 Georgia (Cinematic Serif)",
        "intro_animation": "glow_reveal",
        "chapter_animation": "bracket_frame",
        "outro_animation": "gradient_pulse_border",
        "intro_start_tracking": 30,
        "intro_end_tracking": 6,
        "fill_style": "solid",
        "gradient_colors": ((255, 255, 255), (220, 220, 240)),
        "gradient_angle": 0,
        "glow": False,
        "intro_glow_color": (150, 180, 220),
        "intro_glow_radius": 10,
        "bg_depth_treatment": "vignette_patch",
        "chapter_card_position": "center",
        "chapter_card_bg_color": (0, 0, 0, 170),
        "chapter_card_accent_color": (255, 255, 255),
        "outro_accent_color": (200, 200, 220),
    },
}


def get_overlay_preset(name: str) -> dict:
    """Retrieves preset parameters by name or returns default Cinematic Warm."""
    if not name or name not in OVERLAY_PRESETS:
        return dict(OVERLAY_PRESETS["🎬 Cinematic Warm"])
    return dict(OVERLAY_PRESETS[name])
