"""
modules/fact_text_overlay.py
─────────────────────────────────────────────────────────────────────────────
Fact Text Overlay Engine for Pixelab.

Renders approved extracted facts directly on top of video frames as STYLED TEXT ONLY.
NO background panel, NO box, NO card, NO semi-transparent rectangle behind the text.
Just the pure text itself, rendered with Hollywood-grade typography:
  • Font resolution via LRU-cached get_cached_font()
  • Solid or 2-Stop Linear Gradient text fill
  • Mandatory dark drop shadow & dark outline stroke for high contrast on bright video
  • Animatable letter tracking compression keyframes (start_tracking -> end_tracking)
  • Entrance & Exit Animations (Fade, Slide Up/Down, Tracking, Word Reveal)
  • Flexible screen positioning (Top, Center, Bottom, Custom-Y%)
─────────────────────────────────────────────────────────────────────────────
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from modules.easing import ease_out_back, ease_out_quad, clamp
from modules.subtitle_vfx import (
    get_cached_font,
    measure_text_with_spacing,
    draw_text_with_spacing,
    hex_to_rgb,
)
from modules.title_overlay import render_gradient_text


def apply_fact_text_overlay(frame: np.ndarray, t: float, duration: float, config: dict) -> np.ndarray:
    """
    Called per-frame. Draws the current fact as text only, no background box.
    Returns modified frame. If config["fact_text"] is empty, returns frame unchanged.
    """
    fact_text = str(config.get("fact_text") or "").strip()
    if not fact_text:
        return frame

    display_duration = float(config.get("display_duration", duration or 2.5))
    if t > display_duration or t < 0:
        return frame

    try:
        h, w = frame.shape[:2]

        # ── 1. CONFIG RESOLUTION & DEFAULTS ──────────────────────────────────
        font_family = str(config.get("fact_font_family") or config.get("card_font_family") or "DejaVuSans-Bold.ttf")
        font_scale = float(config.get("fact_font_scale", 1.0))
        fact_font_size = max(24, int(h * 0.055 * font_scale))
        font = get_cached_font(font_family, fact_font_size)

        fill_style = str(config.get("fill_style", "solid")).lower()
        solid_color_hex = str(config.get("fact_color", "#FFFFFF"))
        solid_rgb = hex_to_rgb(solid_color_hex)

        grad_colors_raw = config.get("fact_gradient_colors", ["#FFD700", "#FF7828"])
        grad_colors = (
            hex_to_rgb(grad_colors_raw[0] if len(grad_colors_raw) > 0 else "#FFD700"),
            hex_to_rgb(grad_colors_raw[1] if len(grad_colors_raw) > 1 else "#FF7828"),
        )

        start_tracking = int(config.get("start_tracking", 30))
        end_tracking = int(config.get("end_tracking", 6))
        outline_width = max(2, int(config.get("outline_width", 3)))
        shadow_opacity = max(0.3, float(config.get("shadow_opacity", 0.6)))

        position = str(config.get("fact_position", "bottom")).lower()
        custom_y_pct = float(config.get("fact_custom_y_percent", 80.0))

        entrance_anim = str(config.get("entrance_animation", "tracking")).lower()
        exit_anim = str(config.get("exit_animation", "fade")).lower()

        # ── 2. ANIMATION TIMING & PROGRESS RATIOS ─────────────────────────────
        anim_dur = min(0.6, display_duration * 0.3)
        p_in = clamp(t / anim_dur)
        e_in = ease_out_back(p_in)

        # Exit animation ratio (last 0.4s)
        exit_start = max(0.0, display_duration - 0.4)
        if t >= exit_start:
            p_out = clamp((t - exit_start) / 0.4)
        else:
            p_out = 0.0

        # Calculate Opacity & Motion Offsets
        alpha_mult = 1.0
        y_offset = 0.0

        # Entrance
        if entrance_anim == "fade":
            alpha_mult *= clamp(t / anim_dur)
        elif entrance_anim == "slide_up":
            alpha_mult *= clamp(t / anim_dur)
            y_offset += int(40.0 * (1.0 - ease_out_quad(p_in)))
        elif entrance_anim == "slide_down":
            alpha_mult *= clamp(t / anim_dur)
            y_offset -= int(40.0 * (1.0 - ease_out_quad(p_in)))
        elif entrance_anim == "tracking":
            alpha_mult *= clamp(t / (anim_dur * 0.7))

        # Exit
        if exit_anim == "fade":
            alpha_mult *= (1.0 - p_out)
        elif exit_anim == "slide_up":
            alpha_mult *= (1.0 - p_out)
            y_offset -= int(40.0 * p_out)
        elif exit_anim == "slide_down":
            alpha_mult *= (1.0 - p_out)
            y_offset += int(40.0 * p_out)

        alpha_int = int(255 * alpha_mult)
        if alpha_int <= 0:
            return frame

        # Animatable Tracking Compression: wide -> settled
        cur_tracking = int(start_tracking + (end_tracking - start_tracking) * e_in)

        # ── 3. MEASURE TEXT & DETERMINE POSITION ──────────────────────────────
        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay_pil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_pil)

        tw, th = measure_text_with_spacing(draw, fact_text, font, cur_tracking)
        target_x = (w - tw) // 2

        if position == "top":
            target_y = int(h * 0.15)
        elif position == "center":
            target_y = (h - th) // 2
        elif position == "custom":
            target_y = int(h * (custom_y_pct / 100.0)) - (th // 2)
        else:  # bottom (default)
            target_y = int(h * 0.80) - (th // 2)

        target_y = int(target_y + y_offset)

        # ── 4. WORD REVEAL ANIMATION OPTION ──────────────────────────────────
        words = fact_text.split()
        if entrance_anim == "word_reveal" and len(words) > 1:
            visible_count = max(1, int(t / 0.15) + 1)
            display_text = " ".join(words[:visible_count])
            tw, th = measure_text_with_spacing(draw, display_text, font, cur_tracking)
            target_x = (w - tw) // 2
        else:
            display_text = fact_text

        # ── 5. LEGIBILITY: MANDATORY DROP SHADOW & OUTLINE STROKE ─────────────
        # Mandatory Drop Shadow (4px offset, dark black)
        shadow_col = (0, 0, 0, int(255 * shadow_opacity * alpha_mult))
        draw_text_with_spacing(draw, (target_x + 4, target_y + 4), display_text, font, shadow_col, cur_tracking)

        # Mandatory Dark Outline Stroke around glyphs
        stroke_col = (0, 0, 0, alpha_int)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx * dx + dy * dy <= outline_width * outline_width and (dx != 0 or dy != 0):
                    draw_text_with_spacing(draw, (target_x + dx, target_y + dy), display_text, font, stroke_col, cur_tracking)

        # ── 6. TEXT FILL: SOLID OR 2-STOP LINEAR GRADIENT ──────────────────────
        if fill_style == "gradient":
            text_fill_layer = render_gradient_text(
                w, h, display_text, font, (target_x, target_y),
                grad_colors, angle=45.0, letter_spacing=cur_tracking, alpha=alpha_int
            )
            overlay_pil = Image.alpha_composite(overlay_pil, text_fill_layer)
        else:
            # Solid Color Fill
            text_col = (solid_rgb[0], solid_rgb[1], solid_rgb[2], alpha_int)
            draw_text_with_spacing(draw, (target_x, target_y), display_text, font, text_col, cur_tracking)

        final_pil = Image.alpha_composite(base_pil, overlay_pil).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame
