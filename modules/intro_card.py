"""
modules/intro_card.py
─────────────────────────────────────────────────────────────────────────────
Cinematic Intro Title Card Generator for Pixelab.

Provides 4 High-Impact Intro Title Animation Styles:
  1. particle_assemble — Letters assemble from outer positions with alpha fade
  2. glow_reveal       — Soft Gaussian blur bloom unfolding into crisp text
  3. cinematic_scale   — 1.3x scale zoom-in with linear alpha transition
  4. typewriter        — Character-by-character typewriter reveal

Provides 3 Background Styles:
  1. solid_black   — Pure pitch black cinematic background
  2. gradient_dark — Deep slate-to-navy linear gradient
  3. radial_glow   — Center-illuminated radial spotlight

Fully relative sizing & MoviePy v2 compatibility.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import math
import random
import functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import VideoClip

from modules.subtitle_vfx import resolve_font_path, get_cached_font, measure_text_with_spacing, draw_text_with_spacing


def render_intro_background(w: int, h: int, bg_style: str, glow_color: tuple) -> Image.Image:
    bg_style = (bg_style or "radial_glow").lower().replace(" ", "_")
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))

    if bg_style == "solid_black":
        return img

    elif bg_style == "gradient_dark":
        draw = ImageDraw.Draw(img)
        for y in range(h):
            r = int(10 + 20 * (y / float(h)))
            g = int(12 + 25 * (y / float(h)))
            b = int(24 + 40 * (y / float(h)))
            draw.line([(0, y), (w, y)], fill=(r, g, b, 255))
        return img

    else:  # radial_glow (Default)
        Y, X = np.ogrid[:h, :w]
        cx, cy = w / 2.0, h / 2.0
        dist = np.sqrt(((X - cx) / w) ** 2 + ((Y - cy) / h) ** 2)
        glow_r, glow_g, glow_b = glow_color[:3]

        r_chan = np.clip(10 + (glow_r * 0.35) * (1.0 - dist * 1.8), 0, 255).astype(np.uint8)
        g_chan = np.clip(12 + (glow_g * 0.35) * (1.0 - dist * 1.8), 0, 255).astype(np.uint8)
        b_chan = np.clip(20 + (glow_b * 0.35) * (1.0 - dist * 1.8), 0, 255).astype(np.uint8)

        arr = np.dstack((r_chan, g_chan, b_chan, np.full((h, w), 255, dtype=np.uint8)))
        return Image.fromarray(arr, mode="RGBA")


def render_intro_frame(t: float, duration: float, title: str, subtitle: str, config: dict, w: int = 1920, h: int = 1080) -> np.ndarray:
    try:
        title = (title or "PIXELAB").upper().strip()
        subtitle = (subtitle or "").strip()

        bg_style = config.get("intro_bg_style", "radial_glow")
        anim_style = config.get("intro_style_override") or config.get("intro_animation", "glow_reveal")
        anim_style = anim_style.lower().replace(" ", "_")

        title_color = config.get("intro_title_color", (255, 255, 255))
        glow_color = config.get("intro_glow_color", (68, 136, 255))
        glow_radius = max(0, int(config.get("intro_glow_radius", 15)))
        letter_spacing = max(0, int(config.get("intro_letter_spacing", 8)))

        show_subtitle = config.get("intro_show_subtitle", True)
        subtitle_color = config.get("intro_subtitle_color", (153, 153, 204))

        # Relative font sizing
        title_font_size = max(28, int(h * 0.09 * float(config.get("intro_title_size_scale", 1.0))))
        subtitle_font_size = max(18, int(h * 0.04))

        font_file = config.get("font", "DejaVuSans-Bold.ttf")
        font_title = get_cached_font(font_file, title_font_size)
        font_sub = get_cached_font("DejaVuSans.ttf", subtitle_font_size)

        # 1. Base Background
        bg_pil = render_intro_background(w, h, bg_style, glow_color)
        text_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_layer)

        # Calculate dimensions
        title_w, title_h = measure_text_with_spacing(draw, title, font_title, letter_spacing)
        sub_w, sub_h = measure_text_with_spacing(draw, subtitle, font_sub, 2) if (show_subtitle and subtitle) else (0, 0)

        total_h = title_h + (sub_h + 20 if sub_w > 0 else 0)
        center_x = w // 2
        center_y = h // 2
        title_y = center_y - (total_h // 2)

        # Progress ratio
        p = min(max(t / max(duration, 0.1), 0.0), 1.0)
        title_alpha = 255

        # 2. Render Animation Modes
        if anim_style == "particle_assemble":
            # Letters assemble from random offsets
            anim_dur = min(0.8, duration * 0.4)
            anim_p = min(max(t / anim_dur, 0.0), 1.0)
            title_alpha = int(255 * anim_p)

            cur_x = center_x - (title_w // 2)
            for idx, char in enumerate(title):
                bbox = draw.textbbox((0, 0), char, font=font_title)
                cw = bbox[2] - bbox[0]

                random.seed(idx * 777)
                off_x = int((random.randint(-120, 120)) * (1.0 - anim_p))
                off_y = int((random.randint(-150, 150)) * (1.0 - anim_p))

                c_alpha = int(255 * min(1.0, anim_p * 1.4))
                char_col = (title_color[0], title_color[1], title_color[2], c_alpha)
                draw.text((cur_x + off_x, title_y + off_y), char, font=font_title, fill=char_col)
                cur_x += cw + letter_spacing

        elif anim_style == "cinematic_scale":
            # Scale from 1.3x down to 1.0x with smooth alpha transition
            anim_dur = min(0.7, duration * 0.35)
            anim_p = min(max(t / anim_dur, 0.0), 1.0)
            title_alpha = int(255 * min(1.0, anim_p * 1.5))

            scale = 1.30 - 0.30 * anim_p
            scaled_size = max(24, int(title_font_size * scale))
            scaled_font = get_cached_font(font_file, scaled_size)

            sw, sh = measure_text_with_spacing(draw, title, scaled_font, int(letter_spacing * scale))
            sx = center_x - (sw // 2)
            sy = title_y - int((sh - title_h) / 2)

            t_col = (title_color[0], title_color[1], title_color[2], title_alpha)
            draw_text_with_spacing(draw, (sx, sy), title, scaled_font, t_col, int(letter_spacing * scale))

        elif anim_style == "typewriter":
            # Character by character reveal
            n_chars = len(title)
            anim_dur = min(1.2, duration * 0.5)
            reveal_count = max(1, int(n_chars * min(1.0, t / anim_dur)))
            revealed_title = title[:reveal_count]
            if reveal_count < n_chars and int(t * 5) % 2 == 0:
                revealed_title += "|"

            tw, th = measure_text_with_spacing(draw, revealed_title, font_title, letter_spacing)
            tx = center_x - (title_w // 2)
            t_col = (title_color[0], title_color[1], title_color[2], 255)
            draw_text_with_spacing(draw, (tx, title_y), revealed_title, font_title, t_col, letter_spacing)

        else:  # glow_reveal (Default)
            anim_dur = min(0.6, duration * 0.3)
            anim_p = min(max(t / anim_dur, 0.0), 1.0)
            title_alpha = int(255 * anim_p)

            tx = center_x - (title_w // 2)
            t_col = (title_color[0], title_color[1], title_color[2], title_alpha)
            draw_text_with_spacing(draw, (tx, title_y), title, font_title, t_col, letter_spacing)

        # 3. Glow Layer Bloom
        if glow_radius > 0 and title_alpha > 10:
            glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow_layer)
            tx = center_x - (title_w // 2)
            g_col = (glow_color[0], glow_color[1], glow_color[2], int(glow_color[3] if len(glow_color) > 3 else 220))
            draw_text_with_spacing(g_draw, (tx, title_y), title, font_title, g_col, letter_spacing)
            blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
            text_layer = Image.alpha_composite(blurred_glow, text_layer)
            draw = ImageDraw.Draw(text_layer)

        # 4. Render Subtitle Tagline
        if show_subtitle and subtitle and sub_w > 0:
            sub_delay = min(0.5, duration * 0.25)
            sub_p = min(max((t - sub_delay) / max(0.4, duration * 0.3), 0.0), 1.0)
            sub_alpha = int(255 * sub_p)
            if sub_alpha > 0:
                sub_x = center_x - (sub_w // 2)
                sub_y = title_y + title_h + 20
                s_col = (subtitle_color[0], subtitle_color[1], subtitle_color[2], sub_alpha)
                draw_text_with_spacing(draw, (sub_x, sub_y), subtitle, font_sub, s_col, 2)

        final_pil = Image.alpha_composite(bg_pil, text_layer).convert("RGB")
        return np.array(final_pil)

    except Exception as err:
        # Robust fallback
        black = np.zeros((h, w, 3), dtype=np.uint8)
        return black


def generate_intro_clip(title: str, subtitle: str, config: dict) -> VideoClip:
    """
    Generates a full MoviePy VideoClip for the intro title sequence.
    MoviePy v2 syntax compliant.
    """
    duration = float(config.get("intro_duration", 3.0))
    res_key = config.get("resolution", "1920×1080 (Full HD)")
    
    # Resolve dimensions
    from modules.compositor import RESOLUTION_MAP
    w, h = RESOLUTION_MAP.get(res_key, (1920, 1080))
    fps = int(config.get("fps", 24))

    def make_frame(t):
        return render_intro_frame(t, duration, title, subtitle, config, w=w, h=h)

    clip = VideoClip(make_frame=make_frame, duration=duration)
    return clip.with_fps(fps)
