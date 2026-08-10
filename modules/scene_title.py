"""
modules/scene_title.py
─────────────────────────────────────────────────────────────────────────────
Chapter Title Card Overlay Engine for Pixelab.

Overlay function applied during the first 2.5 seconds of a chapter scene.

Provides 4 Entry Animation Styles:
  1. slide_horizontal — Card slides smoothly from left off-screen into position
  2. slide_vertical   — Card slides smoothly up from bottom into position
  3. fade             — Card fades in with smooth alpha transition
  4. wipe             — Card un-wipes horizontally from left to right

Position Anchors: center, lower_third, upper_third
Full relative sizing & error fallback.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from modules.subtitle_vfx import get_cached_font, measure_text_with_spacing, draw_text_with_spacing


def apply_scene_title(frame: np.ndarray, t: float, chapter_title: str, config: dict) -> np.ndarray:
    """
    Applies a sleek Chapter Title Card overlay on top of frame during the first 2.5 seconds of a scene.
    """
    if not chapter_title or not str(chapter_title).strip():
        return frame

    # Show overlay only for the first 2.5 seconds
    overlay_duration = 2.5
    if t > overlay_duration:
        return frame

    try:
        h, w = frame.shape[:2]
        chapter_title = str(chapter_title).upper().strip()

        anim_style = config.get("chapter_card_style", "slide_horizontal").lower().replace(" ", "_")
        pos_anchor = config.get("chapter_card_position", "center").lower().replace(" ", "_")

        bg_rgba = config.get("chapter_card_bg_color", (0, 0, 0, 180))
        text_color = config.get("chapter_card_text_color", (255, 255, 255))
        accent_color = config.get("chapter_card_accent_color", (68, 136, 255))
        show_lines = config.get("chapter_card_show_lines", True)

        font_size = max(20, int(h * 0.065))
        font = get_cached_font(config.get("font", "DejaVuSans-Bold.ttf"), font_size)

        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay_pil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_pil)

        # Measure text
        tw, th = measure_text_with_spacing(draw, chapter_title, font, 2)
        card_w = tw + 60
        card_h = th + 36

        # Determine Target Anchor Position
        if pos_anchor == "upper_third":
            target_y = int(h * 0.25) - (card_h // 2)
        elif pos_anchor == "lower_third":
            target_y = int(h * 0.75) - (card_h // 2)
        else:  # center
            target_y = int(h * 0.50) - (card_h // 2)

        target_x = (w - card_w) // 2

        # ── Animation Progress (Entrance 0-0.4s, Exit 2.1-2.5s) ──
        if t < 0.4:
            p_in = min(max(t / 0.4, 0.0), 1.0)
            p_out = 1.0
        elif t > 2.1:
            p_in = 1.0
            p_out = min(max(1.0 - (t - 2.1) / 0.4, 0.0), 1.0)
        else:
            p_in = 1.0
            p_out = 1.0

        alpha_scale = p_out
        draw_x = target_x
        draw_y = target_y
        clip_wipe_w = card_w

        if anim_style == "slide_horizontal":
            # Slide in from left
            start_x = -card_w
            draw_x = int(start_x + (target_x - start_x) * p_in)

        elif anim_style == "slide_vertical":
            # Slide in from bottom
            start_y = h + card_h
            draw_y = int(start_y - (start_y - target_y) * p_in)

        elif anim_style == "wipe":
            # Un-wipe left to right
            clip_wipe_w = int(card_w * p_in)

        else:  # fade (Default)
            alpha_scale = p_in * p_out

        if alpha_scale <= 0:
            return frame

        # Apply alpha scale to colors
        eff_bg = (bg_rgba[0], bg_rgba[1], bg_rgba[2], int((bg_rgba[3] if len(bg_rgba) > 3 else 180) * alpha_scale))
        eff_text = (text_color[0], text_color[1], text_color[2], int(255 * alpha_scale))
        eff_accent = (accent_color[0], accent_color[1], accent_color[2], int(255 * alpha_scale))

        # Render Rounded Card Box
        if anim_style == "wipe" and clip_wipe_w < card_w:
            w_box = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            w_draw = ImageDraw.Draw(w_box)
            w_draw.rounded_rectangle([0, 0, card_w, card_h], radius=12, fill=eff_bg, outline=eff_accent, width=2)
            if show_lines:
                w_draw.rectangle([0, 0, 8, card_h], fill=eff_accent)
            w_draw.text((30, 18), chapter_title, font=font, fill=eff_text)
            
            # Crop wipe portion
            w_box_cropped = w_box.crop((0, 0, clip_wipe_w, card_h))
            overlay_pil.paste(w_box_cropped, (draw_x, draw_y), w_box_cropped)
        else:
            draw.rounded_rectangle([draw_x, draw_y, draw_x + card_w, draw_y + card_h], radius=12, fill=eff_bg, outline=eff_accent, width=2)
            if show_lines:
                draw.rounded_rectangle([draw_x + 3, draw_y + 3, draw_x + 10, draw_y + card_h - 3], radius=3, fill=eff_accent)
                draw.line([(draw_x + card_w - 40, draw_y + card_h - 8), (draw_x + card_w - 15, draw_y + card_h - 8)], fill=eff_accent, width=3)
            
            draw_text_with_spacing(draw, (draw_x + 30, draw_y + 18), chapter_title, font, eff_text, 2)

        final_pil = Image.alpha_composite(base_pil, overlay_pil).convert("RGB")
        return np.array(final_pil)

    except Exception:
        # Return unmodified frame on error
        return frame
