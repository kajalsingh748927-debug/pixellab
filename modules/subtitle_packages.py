"""
modules/subtitle_packages.py
─────────────────────────────────────────────────────────────────────────────
Subtitle Preset Packages Engine for Pixelab.

Provides 10 Industry-Standard Subtitle Packages:
  1. 🔥 Hormozi Kinetic
  2. 💥 MrBeast Impact
  3. ⚡ Cyberpunk Glitch
  4. ✨ Opus Glow
  5. 🍿 Cinema Minimalist
  6. 🗯️ Comic Boom
  7. 📰 News Breaking Ticker
  8. 🎤 Karaoke Wave
  9. 🔮 Neon Synthwave
 10. ⌨️ Typewriter Retro
─────────────────────────────────────────────────────────────────────────────
"""

SUBTITLE_PACKAGES = {
    "🔥 Hormozi Kinetic": {
        "active_color": (255, 235, 59),       # Kinetic Yellow
        "inactive_color": (255, 255, 255),    # Pure White
        "stroke_color": (0, 0, 0),
        "stroke_width": 5,
        "active_stroke_color": None,
        "box_bg": None,                        # Clean transparent background
        "box_border": None,
        "animation": "Scale Pop",
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Bottom",
        "size": "Medium",
        "enable_emojis": True,
        "chunk_size": 3,
    },

    "💥 MrBeast Impact": {
        "active_color": (255, 220, 0),        # Bright Yellow
        "inactive_color": (0, 255, 255),      # Neon Cyan
        "stroke_color": (0, 0, 0),
        "stroke_width": 6,
        "active_stroke_color": (220, 0, 0),    # Red Stroke on Active
        "box_bg": None,
        "box_border": None,
        "animation": "Spring Bounce",
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Center",
        "size": "Large",
        "enable_emojis": True,
        "chunk_size": 2,
    },

    "⚡ Cyberpunk Glitch": {
        "active_color": (0, 255, 255),        # Cyan
        "inactive_color": (255, 255, 255),
        "stroke_color": (0, 0, 0),
        "stroke_width": 5,
        "active_stroke_color": (255, 0, 128),  # Magenta Outline
        "box_bg": None,
        "box_border": None,
        "animation": "Glitch Shake",
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Lower Center",
        "size": "Medium",
        "enable_emojis": False,
        "chunk_size": 3,
    },

    "✨ Opus Glow": {
        "active_color": (255, 255, 255),
        "inactive_color": (160, 160, 180),
        "stroke_color": (20, 20, 40),
        "stroke_width": 4,
        "active_stroke_color": None,
        "box_bg": None,
        "box_border": None,
        "animation": "Soft Glow",
        "font_file": "DejaVuSans.ttf",
        "position": "Lower Center",
        "size": "Medium",
        "enable_emojis": True,
        "chunk_size": 4,
    },

    "🍿 Cinema Minimalist": {
        "active_color": (245, 240, 220),       # Off-white / Gold Cream
        "inactive_color": (170, 170, 170),
        "stroke_color": (10, 10, 10),
        "stroke_width": 3,
        "active_stroke_color": None,
        "box_bg": None,
        "box_border": None,
        "animation": "Fade In Words",
        "font_file": "DejaVuSerif-Bold.ttf",
        "position": "Bottom",
        "size": "Small",
        "enable_emojis": False,
        "chunk_size": 5,
    },

    "🗯️ Comic Boom": {
        "active_color": (255, 230, 0),        # Comic Yellow
        "inactive_color": (255, 255, 255),
        "stroke_color": (0, 0, 0),
        "stroke_width": 7,
        "active_stroke_color": (255, 50, 50),
        "box_bg": None,
        "box_border": None,
        "animation": "Spring Bounce",
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Upper Center",
        "size": "Large",
        "enable_emojis": True,
        "chunk_size": 3,
    },

    "📰 News Breaking Ticker": {
        "active_color": (255, 255, 255),
        "inactive_color": (220, 220, 220),
        "stroke_color": (0, 0, 0),
        "stroke_width": 3,
        "active_stroke_color": None,
        "box_bg": (180, 0, 0, 230),            # Breaking Red Banner
        "box_border": (255, 255, 255, 200),
        "animation": "All White (No Animation)",
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Bottom",
        "size": "Medium",
        "enable_emojis": False,
        "chunk_size": 6,
    },

    "🎤 Karaoke Wave": {
        "active_color": (0, 255, 128),         # Emerald Green Active
        "inactive_color": (255, 255, 255),
        "stroke_color": (0, 0, 0),
        "stroke_width": 4,
        "active_stroke_color": None,
        "box_bg": None,
        "box_border": None,
        "animation": "Karaoke Underline",
        "font_file": "DejaVuSans-Bold.ttf",
        "position": "Lower Center",
        "size": "Medium",
        "enable_emojis": True,
        "chunk_size": 4,
    },

    "🔮 Neon Synthwave": {
        "active_color": (255, 0, 220),        # Hot Pink
        "inactive_color": (120, 220, 255),     # Electric Cyan
        "stroke_color": (30, 0, 50),
        "stroke_width": 5,
        "active_stroke_color": (0, 255, 255),
        "box_bg": None,
        "box_border": None,
        "animation": "Scale Pop",
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Center",
        "size": "Medium",
        "enable_emojis": False,
        "chunk_size": 3,
    },

    "⌨️ Typewriter Retro": {
        "active_color": (50, 255, 50),        # Matrix Green Text
        "inactive_color": (30, 180, 30),
        "stroke_color": (0, 20, 0),
        "stroke_width": 3,
        "active_stroke_color": None,
        "box_bg": None,
        "box_border": None,
        "animation": "Fade In Words",
        "font_file": "DejaVuSansMono-Bold.ttf",
        "position": "Bottom",
        "size": "Small",
        "enable_emojis": False,
        "chunk_size": 5,
    },
}



def get_subtitle_package(package_name: str) -> dict:
    """Returns the package config dict or defaults to Hormozi Kinetic."""
    return SUBTITLE_PACKAGES.get(package_name, SUBTITLE_PACKAGES["🔥 Hormozi Kinetic"])
