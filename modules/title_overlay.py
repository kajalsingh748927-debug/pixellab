"""
modules/title_overlay.py
─────────────────────────────────────────────────────────────────────────────
Unified Direct Video Title & CTA Overlay Engine for Pixelab.

CRITICAL ARCHITECTURE:
  • ALL text and graphics are OVERLAID directly on top of real stock video footage.
  • REAL VIDEO is ALWAYS visible underneath (no separate black background clips).
  • Rendered per-frame via MoviePy `clip.transform()`.

Functions:
  1. apply_intro_overlay   — Drawn on Scene 1 for first intro_duration seconds
  2. apply_chapter_overlay — Drawn on chapter scenes for first 2.5 seconds
  3. apply_outro_overlay   — Drawn on last scene for last outro_duration seconds
─────────────────────────────────────────────────────────────────────────────
"""
import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from modules.subtitle_vfx import get_cached_font, measure_text_with_spacing, draw_text_with_spacing, hex_to_rgb


# ── 1. INTRO TITLE OVERLAY (ON SCENE 1) ───────────────────────────────────────
def apply_intro_overlay(frame: np.ndarray, t: float, intro_data: dict, config: dict) -> np.ndarray:
    """
    Draws intro title text OVER real video frame.
    Called on Scene 1 frames for the first intro_duration seconds.
    """
    duration = float(config.get("intro_duration", 3.0))
    if t > duration:
        return frame

    try:
        h, w = frame.shape[:2]

        intro_data = intro_data or {}
        title = str(config.get("intro_title_override") or intro_data.get("title") or "PIXELAB").upper().strip()
        subtitle = str(config.get("intro_subtitle_override") or intro_data.get("subtitle") or "").strip()

        anim_style = (config.get("intro_style_override") or config.get("intro_animation", "glow_reveal")).lower().replace(" ", "_")
        title_color = config.get("intro_title_color", (255, 255, 255))
        glow_color = config.get("intro_glow_color", (68, 136, 255))
        glow_radius = max(0, int(config.get("intro_glow_radius", 15)))
        letter_spacing = max(0, int(config.get("intro_letter_spacing", 8)))

        show_subtitle = config.get("intro_show_subtitle", True)
        subtitle_color = config.get("intro_subtitle_color", (153, 153, 204))

        if isinstance(title_color, str) and title_color.startswith("#"):
            title_color = hex_to_rgb(title_color)
        if isinstance(glow_color, str) and glow_color.startswith("#"):
            glow_color = hex_to_rgb(glow_color)
        if isinstance(subtitle_color, str) and subtitle_color.startswith("#"):
            subtitle_color = hex_to_rgb(subtitle_color)

        title_font_size = max(28, int(h * 0.09 * float(config.get("intro_title_size_scale", 1.0))))
        subtitle_font_size = max(18, int(h * 0.04))

        font_file = config.get("font", "DejaVuSans-Bold.ttf")
        font_title = get_cached_font(font_file, title_font_size)
        font_sub = get_cached_font("DejaVuSans.ttf", subtitle_font_size)

        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        title_w, title_h = measure_text_with_spacing(draw, title, font_title, letter_spacing)
        sub_w, sub_h = measure_text_with_spacing(draw, subtitle, font_sub, 2) if (show_subtitle and subtitle) else (0, 0)

        center_x = w // 2
        center_y = h // 2
        title_y = center_y - (title_h // 2)

        # Entrance progress ratio (0 to 1 over first 0.6s)
        p = min(max(t / max(duration, 0.1), 0.0), 1.0)
        title_alpha = int(255 * min(1.0, t / 0.5))

        # Helper to draw dark outline & shadow for 100% video readability
        def draw_readable_text(draw_ctx, pos, txt, font_obj, fill_col, l_space):
            rx, ry = pos
            # 1. Dark Drop Shadow
            sh_col = (0, 0, 0, int(fill_col[3] * 0.85)) if len(fill_col) > 3 else (0, 0, 0, 200)
            draw_text_with_spacing(draw_ctx, (rx + 4, ry + 4), txt, font_obj, sh_col, l_space)
            # 2. Dark Outline Stroke
            for sx in range(-3, 4):
                for sy in range(-3, 4):
                    if sx*sx + sy*sy <= 9 and (sx != 0 or sy != 0):
                        draw_text_with_spacing(draw_ctx, (rx + sx, ry + sy), txt, font_obj, (0, 0, 0, fill_col[3]), l_space)
            # 3. Main Fill
            draw_text_with_spacing(draw_ctx, (rx, ry), txt, font_obj, fill_col, l_space)

        # Render Title Animations
        if anim_style == "particle_assemble":
            anim_dur = min(0.8, duration * 0.4)
            anim_p = min(max(t / anim_dur, 0.0), 1.0)

            cur_x = center_x - (title_w // 2)
            for idx, char in enumerate(title):
                bbox = draw.textbbox((0, 0), char, font=font_title)
                cw = bbox[2] - bbox[0]

                random.seed(idx * 888)
                off_x = int((random.randint(-140, 140)) * (1.0 - anim_p))
                off_y = int((random.randint(-160, 160)) * (1.0 - anim_p))

                c_alpha = int(255 * min(1.0, anim_p * 1.5))
                char_col = (title_color[0], title_color[1], title_color[2], c_alpha)
                draw_readable_text(draw, (cur_x + off_x, title_y + off_y), char, font_title, char_col, 0)
                cur_x += cw + letter_spacing

        elif anim_style == "cinematic_scale":
            anim_dur = min(0.7, duration * 0.35)
            anim_p = min(max(t / anim_dur, 0.0), 1.0)
            scale = 1.30 - 0.30 * anim_p

            scaled_size = max(24, int(title_font_size * scale))
            scaled_font = get_cached_font(font_file, scaled_size)

            sw, sh = measure_text_with_spacing(draw, title, scaled_font, int(letter_spacing * scale))
            sx = center_x - (sw // 2)
            sy = title_y - int((sh - title_h) / 2)

            t_col = (title_color[0], title_color[1], title_color[2], title_alpha)
            draw_readable_text(draw, (sx, sy), title, scaled_font, t_col, int(letter_spacing * scale))

        elif anim_style == "typewriter":
            n_chars = len(title)
            anim_dur = min(1.2, duration * 0.5)
            reveal_count = max(1, int(n_chars * min(1.0, t / anim_dur)))
            revealed_title = title[:reveal_count]
            if reveal_count < n_chars and int(t * 5) % 2 == 0:
                revealed_title += "|"

            tx = center_x - (title_w // 2)
            t_col = (title_color[0], title_color[1], title_color[2], 255)
            draw_readable_text(draw, (tx, title_y), revealed_title, font_title, t_col, letter_spacing)

        else:  # glow_reveal (Default)
            tx = center_x - (title_w // 2)
            t_col = (title_color[0], title_color[1], title_color[2], title_alpha)
            draw_readable_text(draw, (tx, title_y), title, font_title, t_col, letter_spacing)

        # Glow Layer Bloom
        if glow_radius > 0 and title_alpha > 10:
            glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow_layer)
            tx = center_x - (title_w // 2)
            g_col = (glow_color[0], glow_color[1], glow_color[2], int(glow_color[3] if len(glow_color) > 3 else 220))
            draw_text_with_spacing(g_draw, (tx, title_y), title, font_title, g_col, letter_spacing)
            blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
            overlay = Image.alpha_composite(blurred_glow, overlay)
            draw = ImageDraw.Draw(overlay)

        # Subtitle Tagline (70px below title)
        if show_subtitle and subtitle and sub_w > 0:
            sub_delay = min(0.4, duration * 0.2)
            sub_p = min(max((t - sub_delay) / max(0.4, duration * 0.3), 0.0), 1.0)
            sub_alpha = int(255 * sub_p)
            if sub_alpha > 0:
                sub_x = center_x - (sub_w // 2)
                sub_y = title_y + title_h + int(h * 0.065)
                s_col = (subtitle_color[0], subtitle_color[1], subtitle_color[2], sub_alpha)
                draw_readable_text(draw, (sub_x, sub_y), subtitle, font_sub, s_col, 2)

        final_pil = Image.alpha_composite(base_pil, overlay).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame


# ── 2. CHAPTER TITLE OVERLAY ──────────────────────────────────────────────────
def apply_chapter_overlay(frame: np.ndarray, t: float, chapter_title: str, config: dict) -> np.ndarray:
    """
    Draws Chapter Title Card overlay on top of real video frame for first 2.5 seconds.
    """
    if not chapter_title or not str(chapter_title).strip() or t > 2.5:
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

        tw, th = measure_text_with_spacing(draw, chapter_title, font, 2)
        card_w = tw + 60
        card_h = th + 36

        if pos_anchor == "upper_third":
            target_y = int(h * 0.25) - (card_h // 2)
        elif pos_anchor == "lower_third":
            target_y = int(h * 0.75) - (card_h // 2)
        else:
            target_y = int(h * 0.50) - (card_h // 2)

        target_x = (w - card_w) // 2

        # Entrance 0-0.4s, Exit 2.1-2.5s
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
            start_x = -card_w
            draw_x = int(start_x + (target_x - start_x) * p_in)
        elif anim_style == "slide_vertical":
            start_y = h + card_h
            draw_y = int(start_y - (start_y - target_y) * p_in)
        elif anim_style == "wipe":
            clip_wipe_w = int(card_w * p_in)
        else:  # fade
            alpha_scale = p_in * p_out

        if alpha_scale <= 0:
            return frame

        eff_bg = (bg_rgba[0], bg_rgba[1], bg_rgba[2], int((bg_rgba[3] if len(bg_rgba) > 3 else 180) * alpha_scale))
        eff_text = (text_color[0], text_color[1], text_color[2], int(255 * alpha_scale))
        eff_accent = (accent_color[0], accent_color[1], accent_color[2], int(255 * alpha_scale))

        if anim_style == "wipe" and clip_wipe_w < card_w:
            w_box = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            w_draw = ImageDraw.Draw(w_box)
            w_draw.rounded_rectangle([0, 0, card_w, card_h], radius=12, fill=eff_bg, outline=eff_accent, width=2)
            if show_lines:
                w_draw.rectangle([0, 0, 8, card_h], fill=eff_accent)
            w_draw.text((30, 18), chapter_title, font=font, fill=eff_text)
            
            w_box_cropped = w_box.crop((0, 0, clip_wipe_w, card_h))
            overlay_pil.paste(w_box_cropped, (draw_x, draw_y), w_box_cropped)
        else:
            draw.rounded_rectangle([draw_x, draw_y, draw_x + card_w, draw_y + card_h], radius=12, fill=eff_bg, outline=eff_accent, width=2)
            if show_lines:
                draw.rounded_rectangle([draw_x + 3, draw_y + 3, draw_x + 10, draw_y + card_h - 3], radius=3, fill=eff_accent)
            draw_text_with_spacing(draw, (draw_x + 30, draw_y + 18), chapter_title, font, eff_text, 2)

        final_pil = Image.alpha_composite(base_pil, overlay_pil).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame


# ── 3. OUTRO CTA OVERLAY (ON LAST SCENE) ──────────────────────────────────────
def apply_outro_overlay(frame: np.ndarray, t: float, scene_duration: float, outro_data: dict, config: dict) -> np.ndarray:
    """
    Draws Outro CTA text & pulsing button OVER real video frame.
    Called on the LAST scene during its final outro_duration seconds.
    """
    outro_dur = float(config.get("outro_duration", 4.0))
    start_t = max(0.0, scene_duration - outro_dur)
    if t < start_t:
        return frame

    try:
        h, w = frame.shape[:2]
        rel_t = t - start_t
        p_fade = min(max(rel_t / 0.4, 0.0), 1.0)
        alpha = int(255 * p_fade)

        outro_data = outro_data or {}
        thanks_text = str(config.get("outro_thanks_text") or outro_data.get("thanks_text") or "THANKS FOR WATCHING!").upper().strip()
        cta_text = str(config.get("outro_cta_override") or outro_data.get("cta_text") or "LIKE & SUBSCRIBE FOR MORE").upper().strip()
        channel_name = str(config.get("outro_channel_name") or "@YourChannel").strip()

        accent_color = config.get("outro_accent_color", (255, 0, 0))
        show_subscribe = config.get("outro_show_subscribe", True)
        show_like = config.get("outro_show_like", True)

        if isinstance(accent_color, str) and accent_color.startswith("#"):
            accent_color = hex_to_rgb(accent_color)

        font_thanks_size = max(24, int(h * 0.070))
        font_cta_size = max(18, int(h * 0.045))
        font_channel_size = max(16, int(h * 0.040))
        font_btn_size = max(16, int(h * 0.038))

        font_thanks = get_cached_font(config.get("font", "DejaVuSans-Bold.ttf"), font_thanks_size)
        font_cta = get_cached_font("DejaVuSans-Bold.ttf", font_cta_size)
        font_channel = get_cached_font("DejaVuSansMono-Bold.ttf", font_channel_size)

        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        th_w, th_h = measure_text_with_spacing(draw, thanks_text, font_thanks, 4)
        cta_w, cta_h = measure_text_with_spacing(draw, cta_text, font_cta, 2)
        ch_w, ch_h = measure_text_with_spacing(draw, channel_name, font_channel, 2)

        center_x = w // 2
        cur_y = int(h * 0.18)

        def draw_readable_text(draw_ctx, pos, txt, font_obj, fill_col, l_space):
            rx, ry = pos
            sh_col = (0, 0, 0, int(fill_col[3] * 0.85)) if len(fill_col) > 3 else (0, 0, 0, 200)
            draw_text_with_spacing(draw_ctx, (rx + 4, ry + 4), txt, font_obj, sh_col, l_space)
            for sx in range(-3, 4):
                for sy in range(-3, 4):
                    if sx*sx + sy*sy <= 9 and (sx != 0 or sy != 0):
                        draw_text_with_spacing(draw_ctx, (rx + sx, ry + sy), txt, font_obj, (0, 0, 0, fill_col[3]), l_space)
            draw_text_with_spacing(draw_ctx, (rx, ry), txt, font_obj, fill_col, l_space)

        # 1. Thanks Heading
        th_x = center_x - (th_w // 2)
        draw_readable_text(draw, (th_x, cur_y), thanks_text, font_thanks, (255, 255, 255, alpha), 4)
        cur_y += th_h + int(h * 0.04)

        # 2. Call-To-Action Text
        cta_x = center_x - (cta_w // 2)
        draw_readable_text(draw, (cta_x, cur_y), cta_text, font_cta, (230, 230, 250, alpha), 2)
        cur_y += cta_h + int(h * 0.05)

        # 3. Pulsing Subscribe Button
        if show_subscribe:
            btn_text = "SUBSCRIBE"
            pulse_period = 1.5
            pulse_scale = 1.0 + 0.03 * math.sin((2.0 * math.pi * rel_t) / pulse_period)

            btn_font_s = max(16, int(font_btn_size * pulse_scale))
            btn_font_curr = get_cached_font("DejaVuSans-Bold.ttf", btn_font_s)
            bw, bh = measure_text_with_spacing(draw, btn_text, btn_font_curr, 2)

            pad_x, pad_y = 36, 16
            btn_w = bw + pad_x * 2
            btn_h = bh + pad_y * 2
            btn_x = center_x - (btn_w // 2)

            btn_bg = (accent_color[0], accent_color[1], accent_color[2], alpha)
            draw.rounded_rectangle([btn_x, cur_y, btn_x + btn_w, cur_y + btn_h], radius=25, fill=btn_bg, outline=(0, 0, 0, alpha), width=2)

            btn_tx = btn_x + pad_x
            btn_ty = cur_y + pad_y
            draw_text_with_spacing(draw, (btn_tx, btn_ty), btn_text, btn_font_curr, (255, 255, 255, alpha), 2)

            cur_y += btn_h + int(h * 0.05)

        # 4. Like & Share Badges
        if show_like:
            like_badge = "👍 LIKE   🔔 NOTIFY   ↗ SHARE"
            lw, lh = measure_text_with_spacing(draw, like_badge, font_channel, 2)
            lx = center_x - (lw // 2)
            draw_readable_text(draw, (lx, cur_y), like_badge, font_channel, (180, 200, 240, alpha), 2)
            cur_y += lh + int(h * 0.04)

        # 5. Channel Handle
        if channel_name:
            cx_x = center_x - (ch_w // 2)
            draw_readable_text(draw, (cx_x, cur_y), channel_name, font_channel, (255, 235, 59, alpha), 2)

        final_pil = Image.alpha_composite(base_pil, overlay).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame
