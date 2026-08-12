"""
modules/subtitle_packages.py
─────────────────────────────────────────────────────────────────────────────
Comprehensive Subtitle Preset Packages Engine for Pixelab.

Defines 10 Industry-Standard Typography Packages:
  1. 🔥 Hormozi Kinetic
  2. 💥 MrBeast Impact
  3. ⚡ Cyberpunk Glitch
  4. ✨ Opus Glow
  5. 🍿 Cinema Minimalist
  6. 🗯️ Comic Boom
  7. 📰 News Ticker
  8. 🎤 Karaoke Wave
  9. 🔮 Neon Synthwave
 10. ⌨️ Typewriter Retro
─────────────────────────────────────────────────────────────────────────────
"""

SUBTITLE_PACKAGES = {
    "🔥 Hormozi Kinetic": {
        "active_color": (255, 235, 59),          # Kinetic Yellow
        "inactive_color": (255, 255, 255),       # Pure White
        "stroke_color": (0, 0, 0),               # Deep Black Stroke
        "stroke_width": 7,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "none",               # Transparent background
        "bg_color": (0, 0, 0, 0),
        "padding_x": 20,
        "padding_y": 10,
        "animation_type": "scale_pop",           # 1.3x size pop on active word
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Bottom",
        "custom_y_pct": 82,
        "layout_mode": "Two Lines",
        "size_scale": 1.40,                      # Prominent bold size
        "chunk_size": 3,
        "shadow": {
            "offset_x": 4,
            "offset_y": 4,
            "color": (0, 0, 0),
            "opacity": 0.8,
            "blur": 2,
        },
        "glow": None,
        "letter_spacing": 0,
        "enable_emojis": True,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "💥 MrBeast Impact": {
        "active_color": (255, 220, 0),          # Bright Yellow
        "inactive_color": (255, 255, 255),       # White
        "stroke_color": (0, 0, 0),               # Black stroke
        "stroke_width": 7,
        "stroke_style": "solid",
        "active_stroke_color": (220, 0, 0),      # Red stroke on active word
        "background_type": "pill",               # Black semi-transparent box
        "bg_color": (0, 0, 0, 175),
        "padding_x": 26,
        "padding_y": 14,
        "animation_type": "bounce",              # Spring bounce (+5px Y offset)
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Center",
        "custom_y_pct": 50,
        "layout_mode": "Word-by-Word",
        "size_scale": 1.55,                      # Ultra impact viral size
        "chunk_size": 1,
        "shadow": {
            "offset_x": 4,
            "offset_y": 4,
            "color": (0, 0, 0),
            "opacity": 0.8,
            "blur": 0,
        },
        "glow": None,
        "letter_spacing": 1,
        "enable_emojis": True,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "⚡ Cyberpunk Glitch": {
        "active_color": (0, 255, 255),          # Cyan
        "inactive_color": (255, 0, 220),         # Magenta
        "stroke_color": (0, 0, 0),
        "stroke_width": 6,
        "stroke_style": "glitch",                # Double offset stroke (+2px cyan / -2px magenta)
        "cyan_offset": 3,
        "magenta_offset": -3,
        "active_stroke_color": None,
        "background_type": "none",
        "bg_color": (0, 0, 0, 0),
        "padding_x": 20,
        "padding_y": 10,
        "animation_type": "shake",               # Glitch shake jitter
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Lower Third",
        "custom_y_pct": 75,
        "layout_mode": "Three Words at a Time",
        "size_scale": 1.35,                      # Cyberpunk bold size
        "chunk_size": 3,
        "shadow": None,
        "glow": {
            "color": (0, 255, 255),
            "radius": 12,
            "opacity": 0.85,
        },
        "letter_spacing": 2,
        "enable_emojis": False,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "✨ Opus Glow": {
        "active_color": (255, 255, 255),        # Pure White
        "inactive_color": (180, 180, 200),       # Soft Slate
        "stroke_color": (20, 20, 40),
        "stroke_width": 3,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "pill",               # Dark transparent pill-shaped box
        "bg_color": (15, 15, 30, 190),
        "padding_x": 28,
        "padding_y": 14,
        "animation_type": "glow",                # Gaussian glow bloom
        "font_file": "DejaVuSans.ttf",
        "position": "Lower Third",
        "custom_y_pct": 75,
        "layout_mode": "Two Lines",
        "size_scale": 1.30,
        "chunk_size": 4,
        "shadow": None,
        "glow": {
            "color": (255, 255, 255),
            "radius": 14,
            "opacity": 0.9,
        },
        "letter_spacing": 1,
        "enable_emojis": True,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "🍿 Cinema Minimalist": {
        "active_color": (255, 255, 255),        # All White
        "inactive_color": (255, 255, 255),
        "stroke_color": (10, 10, 10),
        "stroke_width": 3,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "none",
        "bg_color": (0, 0, 0, 0),
        "padding_x": 18,
        "padding_y": 10,
        "animation_type": "fade_in_word",        # Words before active are 255, active transitions over 0.3s
        "font_file": "DejaVuSerif-Bold.ttf",
        "position": "Bottom",
        "custom_y_pct": 86,
        "layout_mode": "Full Sentence",
        "size_scale": 1.20,
        "chunk_size": 6,
        "shadow": {
            "offset_x": 3,
            "offset_y": 3,
            "color": (0, 0, 0),
            "opacity": 0.7,
            "blur": 2,
        },
        "glow": None,
        "letter_spacing": 0,
        "enable_emojis": False,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "🗯️ Comic Boom": {
        "active_color": "cycle",                 # Color-cycles red/yellow/green per word index
        "inactive_color": (255, 255, 255),       # White
        "stroke_color": (0, 0, 0),
        "stroke_width": 8,
        "stroke_style": "double",                # Inner + outer double stroke
        "active_stroke_color": (255, 50, 50),
        "background_type": "none",
        "bg_color": (0, 0, 0, 0),
        "padding_x": 24,
        "padding_y": 12,
        "animation_type": "tilt",                # Active word tilted +/- 5 degrees
        "tilt_deg": 5,
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Upper Third",
        "custom_y_pct": 25,
        "layout_mode": "Three Words at a Time",
        "size_scale": 1.45,
        "chunk_size": 3,
        "shadow": {
            "offset_x": 5,
            "offset_y": 5,
            "color": (0, 0, 0),
            "opacity": 0.9,
            "blur": 0,
        },
        "glow": None,
        "letter_spacing": 1,
        "enable_emojis": True,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "📰 News Ticker": {
        "active_color": (255, 255, 255),        # All caps white text
        "inactive_color": (240, 240, 240),
        "stroke_color": (0, 0, 0),
        "stroke_width": 3,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "full_width_bar",     # Full-width dark red banner
        "bg_color": (180, 0, 0, 235),
        "padding_x": 30,
        "padding_y": 14,
        "animation_type": "none",                # Static display
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Bottom",
        "custom_y_pct": 88,
        "layout_mode": "Single Line",
        "size_scale": 1.25,
        "chunk_size": 6,
        "align": "left",
        "text_transform": "uppercase",
        "shadow": None,
        "glow": None,
        "letter_spacing": 1,
        "enable_emojis": False,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "🎤 Karaoke Wave": {
        "active_color": (0, 255, 128),          # Emerald Green active fill
        "inactive_color": (220, 220, 220),       # Grey inactive
        "stroke_color": (0, 0, 0),
        "stroke_width": 5,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "none",
        "bg_color": (0, 0, 0, 0),
        "padding_x": 22,
        "padding_y": 12,
        "animation_type": "karaoke_fill",        # Left-to-right color fill within active word
        "underline_bar": True,                   # Progress bar under active word
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Lower Third",
        "custom_y_pct": 75,
        "layout_mode": "Two Lines",
        "size_scale": 1.35,
        "chunk_size": 4,
        "shadow": {
            "offset_x": 3,
            "offset_y": 3,
            "color": (0, 0, 0),
            "opacity": 0.7,
            "blur": 1,
        },
        "glow": None,
        "letter_spacing": 0,
        "enable_emojis": True,
        "cursor_blink": False,
    },

    "🔮 Neon Synthwave": {
        "active_color": (255, 0, 220),          # Hot Pink Active
        "inactive_color": (120, 220, 255),       # Electric Cyan Inactive
        "stroke_color": (30, 0, 50),
        "stroke_width": 5,
        "stroke_style": "solid",
        "active_stroke_color": (0, 255, 255),
        "background_type": "gradient_bar",       # Horizontal dark synthwave gradient
        "bg_color": (20, 0, 40, 190),
        "bg_gradient": ((40, 0, 60, 210), (0, 30, 60, 210)),
        "padding_x": 26,
        "padding_y": 14,
        "animation_type": "scale_pop",
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Center",
        "custom_y_pct": 50,
        "layout_mode": "Two Lines",
        "size_scale": 1.35,
        "chunk_size": 3,
        "shadow": None,
        "glow": {
            "color": (255, 0, 220),
            "radius": 16,
            "opacity": 0.9,
        },
        "letter_spacing": 3,                     # +3px character advance spacing
        "enable_emojis": False,
        "underline_bar": False,
        "cursor_blink": False,
    },

    "⌨️ Typewriter Retro": {
        "active_color": (240, 185, 35),          # Sepia/Amber Active
        "inactive_color": (160, 135, 100),       # Dimmer Amber Inactive
        "stroke_color": (0, 0, 0),
        "stroke_width": 2,
        "stroke_style": "solid",
        "active_stroke_color": None,
        "background_type": "none",
        "bg_color": (0, 0, 0, 0),
        "padding_x": 16,
        "padding_y": 8,
        "animation_type": "typewriter",          # Reveal chars one by one within active word
        "cursor_blink": True,                    # | cursor character after last revealed char
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Bottom",
        "custom_y_pct": 85,
        "layout_mode": "Single Line",
        "size_scale": 1.25,
        "chunk_size": 5,
        "shadow": None,
        "glow": None,
        "letter_spacing": 1,
        "enable_emojis": False,
        "underline_bar": False,
    },
}


def get_subtitle_package(package_name: str) -> dict:
    """Returns the preset dictionary or defaults to Hormozi Kinetic."""
    return SUBTITLE_PACKAGES.get(package_name, SUBTITLE_PACKAGES["🔥 Hormozi Kinetic"])
