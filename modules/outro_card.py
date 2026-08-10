"""
modules/outro_card.py
─────────────────────────────────────────────────────────────────────────────
Cinematic Outro Title Card Generator for Pixelab.

Features:
  1. Thanks Heading & AI-Generated / Custom Call-To-Action Text
  2. Channel Handle Callout (@YourChannel)
  3. Pulsing Subscribe Button (Rounded rectangle radius=25px, pulsing scale 1.0 -> 1.03 -> 1.0 over 1.5s period)
  4. Like, Share & Bell Notification Badges
  5. 2 Background Styles (Solid Black, Gradient Dark)

MoviePy v2 syntax compliant & full relative sizing.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip

from modules.subtitle_vfx import get_cached_font, measure_text_with_spacing, draw_text_with_spacing


def render_outro_frame(t: float, duration: float, thanks_text: str, cta_text: str, channel_name: str, config: dict, w: int = 1920, h: int = 1080) -> np.ndarray:
    try:
        thanks_text = (thanks_text or "THANKS FOR WATCHING!").upper().strip()
        cta_text = (cta_text or config.get("outro_cta_override") or "LIKE & SUBSCRIBE FOR MORE").upper().strip()
        channel_name = (channel_name or config.get("outro_channel_name") or "@YourChannel").strip()

        bg_style = config.get("outro_bg_style", "solid_black").lower().replace(" ", "_")
        accent_color = config.get("outro_accent_color", (255, 0, 0))
        show_subscribe = config.get("outro_show_subscribe", True)
        show_like = config.get("outro_show_like", True)

        # Relative Font Sizing
        font_thanks_size = max(24, int(h * 0.070))
        font_cta_size = max(18, int(h * 0.045))
        font_channel_size = max(16, int(h * 0.040))
        font_btn_size = max(16, int(h * 0.038))

        font_thanks = get_cached_font(config.get("font", "DejaVuSans-Bold.ttf"), font_thanks_size)
        font_cta = get_cached_font("DejaVuSans-Bold.ttf", font_cta_size)
        font_channel = get_cached_font("DejaVuSansMono-Bold.ttf", font_channel_size)
        font_btn = get_cached_font("DejaVuSans-Bold.ttf", font_btn_size)

        # 1. Background Setup
        if bg_style == "gradient_dark":
            arr = np.zeros((h, w, 4), dtype=np.uint8)
            arr[:, :, 3] = 255
            for y in range(h):
                arr[y, :, 0] = int(12 + 20 * (y / float(h)))
                arr[y, :, 1] = int(10 + 15 * (y / float(h)))
                arr[y, :, 2] = int(25 + 40 * (y / float(h)))
            bg_pil = Image.fromarray(arr, mode="RGBA")
        else:  # solid_black
            bg_pil = Image.new("RGBA", (w, h), (0, 0, 0, 255))

        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Progress fade in
        p_fade = min(max(t / 0.4, 0.0), 1.0)
        alpha = int(255 * p_fade)

        # Measure text elements
        th_w, th_h = measure_text_with_spacing(draw, thanks_text, font_thanks, 4)
        cta_w, cta_h = measure_text_with_spacing(draw, cta_text, font_cta, 2)
        ch_w, ch_h = measure_text_with_spacing(draw, channel_name, font_channel, 2)

        center_x = w // 2
        cur_y = int(h * 0.18)

        # 2. Render Thanks Heading
        th_x = center_x - (th_w // 2)
        draw_text_with_spacing(draw, (th_x, cur_y), thanks_text, font_thanks, (255, 255, 255, alpha), 4)
        cur_y += th_h + int(h * 0.04)

        # 3. Render Call-To-Action Text
        cta_x = center_x - (cta_w // 2)
        draw_text_with_spacing(draw, (cta_x, cur_y), cta_text, font_cta, (230, 230, 250, alpha), 2)
        cur_y += cta_h + int(h * 0.05)

        # 4. Render Pulsing Subscribe Button (scale 1.0 -> 1.03 -> 1.0 over 1.5s period)
        if show_subscribe:
            btn_text = "SUBSCRIBE"
            pulse_period = 1.5
            pulse_scale = 1.0 + 0.03 * math.sin((2.0 * math.pi * t) / pulse_period)

            btn_font_s = max(16, int(font_btn_size * pulse_scale))
            btn_font_curr = get_cached_font("DejaVuSans-Bold.ttf", btn_font_s)
            bw, bh = measure_text_with_spacing(draw, btn_text, btn_font_curr, 2)

            pad_x, pad_y = 36, 16
            btn_w = bw + pad_x * 2
            btn_h = bh + pad_y * 2
            btn_x = center_x - (btn_w // 2)

            btn_bg = (accent_color[0], accent_color[1], accent_color[2], alpha)
            draw.rounded_rectangle([btn_x, cur_y, btn_x + btn_w, cur_y + btn_h], radius=25, fill=btn_bg)

            # Button Text
            btn_tx = btn_x + pad_x
            btn_ty = cur_y + pad_y
            draw_text_with_spacing(draw, (btn_tx, btn_ty), btn_text, btn_font_curr, (255, 255, 255, alpha), 2)

            cur_y += btn_h + int(h * 0.05)

        # 5. Render Like & Share Badges
        if show_like:
            like_badge = "👍 LIKE   🔔 NOTIFY   ↗ SHARE"
            lw, lh = measure_text_with_spacing(draw, like_badge, font_channel, 2)
            lx = center_x - (lw // 2)
            draw_text_with_spacing(draw, (lx, cur_y), like_badge, font_channel, (180, 200, 240, alpha), 2)
            cur_y += lh + int(h * 0.04)

        # 6. Render Channel Handle
        if channel_name:
            cx_x = center_x - (ch_w // 2)
            draw_text_with_spacing(draw, (cx_x, cur_y), channel_name, font_channel, (255, 235, 59, alpha), 2)

        final_pil = Image.alpha_composite(bg_pil, overlay).convert("RGB")
        return np.array(final_pil)

    except Exception:
        # Fallback black frame
        return np.zeros((h, w, 3), dtype=np.uint8)


def generate_outro_clip(thanks_text: str, cta_text: str, channel_name: str, config: dict) -> VideoClip:
    """
    Generates a full MoviePy VideoClip for the outro sequence.
    MoviePy v2 syntax compliant.
    """
    duration = float(config.get("outro_duration", 4.0))
    res_key = config.get("resolution", "1920×1080 (Full HD)")
    
    from modules.compositor import RESOLUTION_MAP
    w, h = RESOLUTION_MAP.get(res_key, (1920, 1080))
    fps = int(config.get("fps", 24))

    def make_frame(t):
        return render_outro_frame(t, duration, thanks_text, cta_text, channel_name, config, w=w, h=h)

    clip = VideoClip(make_frame=make_frame, duration=duration)
    return clip.with_fps(fps)
