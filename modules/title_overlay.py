"""
modules/title_overlay.py
─────────────────────────────────────────────────────────────────────────────
Hollywood-Grade Per-Frame Video Title & Motion Graphics Overlay Engine for Pixelab.

Key Architecture:
  1. Shared TextStyle dataclass powering Intro, Chapter, and Outro overlays
  2. Animatable tracking (letter spacing compression keyframes: start_spacing -> end_spacing)
  3. 2-Stop Gradient Text Fill Engine with angle & sheen sweep
  4. Layered Depth (Localized Gaussian Blur Vignette & Pulsing Accent Glow Blob)
  5. Outer Neon Glow Bloom & Auto-Color Extraction from Video Frames
  6. 6 New Animations: Neon Trace, Split Reveal, Blur-to-Sharp, Bracket Frame, Underline Draw, Gradient Pulse Border

All rendered directly ON TOP of real video frames via MoviePy clip.transform().
─────────────────────────────────────────────────────────────────────────────
"""
import os
import math
import random
import functools
from dataclasses import dataclass
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

from modules.easing import ease_out_back, ease_in_out_expo, spring_overshoot, ease_out_quad, clamp
from modules.subtitle_vfx import get_cached_font, measure_text_with_spacing, draw_text_with_spacing, hex_to_rgb
from modules.overlay_presets import get_overlay_preset


# ── 1. SHARED TEXTSTYLE DATACLASS ─────────────────────────────────────────────
@dataclass
class TextStyle:
    font_file: str = "DejaVuSans-Bold.ttf"
    font_size: int = 64
    start_letter_spacing: int = 36
    end_letter_spacing: int = 8
    word_spacing: int = 10
    line_height: int = 12
    stroke_width: int = 4
    shadow_opacity: float = 0.85
    fill_style: str = "gradient"  # "solid" | "gradient"
    solid_color: tuple = (255, 255, 255)
    gradient_colors: tuple = ((255, 215, 0), (255, 120, 40))
    gradient_angle: float = 45.0
    glow: bool = True
    glow_color: tuple = (255, 140, 0)
    glow_radius: int = 18
    bg_depth: str = "vignette_patch"  # "none" | "vignette_patch" | "glow_blob"


# ── 2. AUTO COLOR EXTRACTION FROM VIDEO FRAME ──────────────────────────────────
def extract_complementary_video_color(frame: np.ndarray) -> tuple:
    """Samples center region of frame and computes a high-contrast complementary accent color."""
    try:
        h, w = frame.shape[:2]
        ch_y1, ch_y2 = int(h * 0.3), int(h * 0.7)
        ch_x1, ch_x2 = int(w * 0.3), int(w * 0.7)
        center_crop = frame[ch_y1:ch_y2, ch_x1:ch_x2]
        avg_r = int(np.mean(center_crop[:, :, 0]))
        avg_g = int(np.mean(center_crop[:, :, 1]))
        avg_b = int(np.mean(center_crop[:, :, 2]))

        # Complementary RGB
        comp_r = 255 - avg_r
        comp_g = 255 - avg_g
        comp_b = 255 - avg_b

        # Boost saturation
        max_c = max(comp_r, comp_g, comp_b, 1)
        comp_r = int(min(255, comp_r * (255.0 / max_c)))
        comp_g = int(min(255, comp_g * (255.0 / max_c)))
        comp_b = int(min(255, comp_b * (255.0 / max_c)))
        return (comp_r, comp_g, comp_b)
    except Exception:
        return (255, 140, 0)


# ── 3. GRADIENT TEXT MASK RENDER HELPER ───────────────────────────────────────
def render_gradient_text(w: int, h: int, text: str, font, pos: tuple, colors: tuple, angle: float = 45.0, letter_spacing: int = 0, alpha: int = 255) -> Image.Image:
    """Renders 2-stop linear gradient text fill with dark outline stroke for max readability."""
    txt_mask = Image.new("L", (w, h), 0)
    m_draw = ImageDraw.Draw(txt_mask)
    draw_text_with_spacing(m_draw, pos, text, font, 255, letter_spacing)

    # Build gradient image
    c1, c2 = colors[0], colors[1]
    grad_arr = np.zeros((h, w, 4), dtype=np.uint8)
    rad = math.radians(angle)
    cos_a, sin_a = math.cos(rad), math.sin(rad)

    Y, X = np.ogrid[:h, :w]
    norm_proj = ((X / float(w)) * cos_a + (Y / float(h)) * sin_a)
    norm_proj = (norm_proj - norm_proj.min()) / max(0.001, (norm_proj.max() - norm_proj.min()))

    grad_arr[:, :, 0] = np.clip(c1[0] * (1.0 - norm_proj) + c2[0] * norm_proj, 0, 255).astype(np.uint8)
    grad_arr[:, :, 1] = np.clip(c1[1] * (1.0 - norm_proj) + c2[1] * norm_proj, 0, 255).astype(np.uint8)
    grad_arr[:, :, 2] = np.clip(c1[2] * (1.0 - norm_proj) + c2[2] * norm_proj, 0, 255).astype(np.uint8)
    grad_arr[:, :, 3] = alpha

    grad_img = Image.fromarray(grad_arr, mode="RGBA")
    text_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    text_rgba.paste(grad_img, (0, 0), txt_mask)
    return text_rgba


# ── 4. LAYERED DEPTH BACKGROUND TREATMENT ─────────────────────────────────────
def render_background_depth_treatment(frame: np.ndarray, center_pos: tuple, block_size: tuple, style: str, accent_color: tuple, t: float = 0.0) -> np.ndarray:
    """Renders localized Gaussian blur vignette patch or pulsing accent glow blob behind text block."""
    if not style or style == "none":
        return frame

    h, w = frame.shape[:2]
    bx, by = center_pos
    bw, bh = block_size
    pad_x, pad_y = int(bw * 0.4), int(bh * 0.5)

    x1, y1 = max(0, bx - (bw // 2) - pad_x), max(0, by - (bh // 2) - pad_y)
    x2, y2 = min(w, bx + (bw // 2) + pad_x), min(h, by + (bh // 2) + pad_y)
    rw, rh = x2 - x1, y2 - y1

    if rw <= 0 or rh <= 0:
        return frame

    img = Image.fromarray(frame).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    if style == "glow_blob":
        pulse = 0.85 + 0.15 * math.sin(t * 4.0)
        blob_col = (accent_color[0], accent_color[1], accent_color[2], int(140 * pulse))
        draw.ellipse([x1, y1, x2, y2], fill=blob_col)
        blurred_layer = layer.filter(ImageFilter.GaussianBlur(radius=int(rw * 0.3)))
        img = Image.alpha_composite(img, blurred_layer)

    elif style == "vignette_patch":
        draw.ellipse([x1, y1, x2, y2], fill=(0, 0, 0, 180))
        blurred_layer = layer.filter(ImageFilter.GaussianBlur(radius=int(rw * 0.25)))
        img = Image.alpha_composite(img, blurred_layer)

    return np.array(img.convert("RGB"))


# ── 5. ADVANCED INTRO TITLE OVERLAY (ON SCENE 1) ──────────────────────────────
def apply_intro_overlay(frame: np.ndarray, t: float, intro_data: dict, config: dict) -> np.ndarray:
    """
    Draws Intro Title & Subtitle with TextStyle, tracking compression keyframes,
    gradient fills, outer neon glow, and 7 animation styles over real video frame.
    """
    duration = float(config.get("intro_duration", 4.0))
    if t > duration:
        return frame

    try:
        h, w = frame.shape[:2]

        # Resolve Theme Preset
        preset_name = config.get("overlay_preset", "🎬 Cinematic Warm")
        preset = get_overlay_preset(preset_name)

        intro_data = intro_data or {}
        raw_override = str(config.get("intro_title_override") or "").strip()
        raw_data_title = str(intro_data.get("title") or "").strip() if isinstance(intro_data, dict) else ""
        title = (raw_override or raw_data_title or "PIXELAB").upper().strip()

        raw_sub_override = str(config.get("intro_subtitle_override") or "").strip()
        raw_data_sub = str(intro_data.get("subtitle") or "").strip() if isinstance(intro_data, dict) else ""
        subtitle = (raw_sub_override or raw_data_sub or "AI VIDEO GENERATOR").strip()

        anim_style = (config.get("intro_style_override") or preset.get("intro_animation", "blur_to_sharp")).lower().replace(" ", "_")

        # Auto Color Extraction
        if config.get("auto_color_from_video"):
            accent_color = extract_complementary_video_color(frame)
            grad_colors = (accent_color, (255, 255, 255))
        else:
            grad_colors = config.get("gradient_colors", preset.get("gradient_colors", ((255, 215, 0), (255, 120, 40))))
            accent_color = grad_colors[0]

        start_tracking = int(config.get("intro_start_tracking", preset.get("intro_start_tracking", 36)))
        end_tracking = int(config.get("intro_end_tracking", preset.get("intro_end_tracking", 8)))
        bg_depth_style = config.get("bg_depth_treatment", preset.get("bg_depth_treatment", "vignette_patch"))

        title_font_size = max(28, int(h * 0.09 * float(config.get("intro_title_size_scale", 1.0))))
        subtitle_font_size = max(18, int(h * 0.04))

        font_file = config.get("font", preset.get("font", "DejaVuSans-Bold.ttf"))
        font_title = get_cached_font(font_file, title_font_size)
        font_sub = get_cached_font("DejaVuSans.ttf", subtitle_font_size)

        # Entrance progress ratio (0 to 1 over first 0.6s)
        anim_dur = min(0.7, duration * 0.4)
        anim_p = clamp(t / anim_dur)
        e_p = ease_out_back(anim_p)

        # Animatable Tracking Compression: wide -> settled
        cur_tracking = int(start_tracking + (end_tracking - start_tracking) * e_p)

        # Measure text block
        test_pil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        test_draw = ImageDraw.Draw(test_pil)
        title_w, title_h = measure_text_with_spacing(test_draw, title, font_title, cur_tracking)
        sub_w, sub_h = measure_text_with_spacing(test_draw, subtitle, font_sub, 2) if subtitle else (0, 0)

        center_x, center_y = w // 2, h // 2
        title_y = center_y - (title_h // 2)

        # 1. Background Depth Layer
        frame = render_background_depth_treatment(frame, (center_x, center_y), (title_w, title_h + 80), bg_depth_style, accent_color, t=t)

        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        title_alpha = int(255 * clamp(t / 0.4))
        draw_x = center_x - (title_w // 2)

        # 2. Render Animation Modes
        if anim_style == "blur_to_sharp":
            # Heavy initial blur + scale settle
            blur_r = int(16.0 * (1.0 - ease_out_quad(anim_p)))
            scale = 1.25 - 0.25 * e_p
            s_size = max(24, int(title_font_size * scale))
            s_font = get_cached_font(font_file, s_size)
            sw, sh = measure_text_with_spacing(draw, title, s_font, cur_tracking)
            sx, sy = center_x - (sw // 2), title_y - int((sh - title_h) / 2)

            t_layer = render_gradient_text(w, h, title, s_font, (sx, sy), grad_colors, angle=45, letter_spacing=cur_tracking, alpha=title_alpha)
            if blur_r > 0:
                t_layer = t_layer.filter(ImageFilter.GaussianBlur(radius=blur_r))
            overlay = Image.alpha_composite(overlay, t_layer)
            draw = ImageDraw.Draw(overlay)

        elif anim_style == "split_reveal":
            # Two halves slide in from left & right, snapping together at center
            mid_i = len(title) // 2
            left_half, right_half = title[:mid_i], title[mid_i:]

            lw, _ = measure_text_with_spacing(draw, left_half, font_title, cur_tracking)
            rw, _ = measure_text_with_spacing(draw, right_half, font_title, cur_tracking)

            off_left = int(-w * 0.4 * (1.0 - e_p))
            off_right = int(w * 0.4 * (1.0 - e_p))

            lx = draw_x + off_left
            rx = draw_x + lw + off_right

            t_left = render_gradient_text(w, h, left_half, font_title, (lx, title_y), grad_colors, angle=45, letter_spacing=cur_tracking, alpha=title_alpha)
            t_right = render_gradient_text(w, h, right_half, font_title, (rx, title_y), grad_colors, angle=45, letter_spacing=cur_tracking, alpha=title_alpha)
            overlay = Image.alpha_composite(overlay, t_left)
            overlay = Image.alpha_composite(overlay, t_right)
            draw = ImageDraw.Draw(overlay)

        elif anim_style == "neon_trace":
            # Outline path draws progressively, then solid gradient fills
            reveal_p = clamp(anim_p * 1.4)
            n_chars = len(title)
            visible_chars = max(1, int(n_chars * reveal_p))
            traced_txt = title[:visible_chars]
            tw, _ = measure_text_with_spacing(draw, traced_txt, font_title, cur_tracking)

            # Stroke trace
            draw_text_with_spacing(draw, (draw_x, title_y), traced_txt, font_title, (accent_color[0], accent_color[1], accent_color[2], title_alpha), cur_tracking)
            if anim_p > 0.5:
                t_layer = render_gradient_text(w, h, title, font_title, (draw_x, title_y), grad_colors, angle=45, letter_spacing=cur_tracking, alpha=int(title_alpha * (anim_p - 0.5) * 2))
                overlay = Image.alpha_composite(overlay, t_layer)
                draw = ImageDraw.Draw(overlay)

        elif anim_style == "particle_assemble":
            cur_x = draw_x
            for idx, char in enumerate(title):
                bbox = draw.textbbox((0, 0), char, font=font_title)
                cw = bbox[2] - bbox[0]
                random.seed(idx * 888)
                off_x = int((random.randint(-140, 140)) * (1.0 - e_p))
                off_y = int((random.randint(-160, 160)) * (1.0 - e_p))

                c_alpha = int(255 * clamp(anim_p * 1.5))
                t_char = render_gradient_text(w, h, char, font_title, (cur_x + off_x, title_y + off_y), grad_colors, angle=45, letter_spacing=0, alpha=c_alpha)
                overlay = Image.alpha_composite(overlay, t_char)
                cur_x += cw + cur_tracking
            draw = ImageDraw.Draw(overlay)

        else:  # glow_reveal (Default)
            t_layer = render_gradient_text(w, h, title, font_title, (draw_x, title_y), grad_colors, angle=45, letter_spacing=cur_tracking, alpha=title_alpha)
            overlay = Image.alpha_composite(overlay, t_layer)
            draw = ImageDraw.Draw(overlay)

        # 3. Outer Neon Glow Bloom Layer
        if config.get("glow", True) and title_alpha > 10:
            glow_radius = max(4, int(config.get("intro_glow_radius", preset.get("intro_glow_radius", 18))))
            glow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            g_draw = ImageDraw.Draw(glow_layer)
            draw_text_with_spacing(g_draw, (draw_x, title_y), title, font_title, (accent_color[0], accent_color[1], accent_color[2], 220), cur_tracking)
            blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_radius))
            overlay = Image.alpha_composite(blurred_glow, overlay)
            draw = ImageDraw.Draw(overlay)

        # 4. Subtitle Tagline (70px below title)
        if subtitle and sub_w > 0:
            sub_p = clamp((t - 0.3) / max(0.4, duration * 0.3))
            sub_alpha = int(255 * sub_p)
            if sub_alpha > 0:
                sub_x = center_x - (sub_w // 2)
                sub_y = title_y + title_h + int(h * 0.065)
                draw_text_with_spacing(draw, (sub_x + 3, sub_y + 3), subtitle, font_sub, (0, 0, 0, int(sub_alpha * 0.8)), 2)
                draw_text_with_spacing(draw, (sub_x, sub_y), subtitle, font_sub, (240, 240, 255, sub_alpha), 2)

        final_pil = Image.alpha_composite(base_pil, overlay).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame


# ── 6. ADVANCED CHAPTER TITLE OVERLAY ─────────────────────────────────────────
def apply_chapter_overlay(frame: np.ndarray, t: float, chapter_title: str, config: dict) -> np.ndarray:
    """
    Draws Chapter Title overlay with Bracket Frame, Underline Draw, and positioning anchors over real video frame.
    """
    if not chapter_title or not str(chapter_title).strip() or t > 2.5:
        return frame

    try:
        h, w = frame.shape[:2]
        preset = get_overlay_preset(config.get("overlay_preset", "🎬 Cinematic Warm"))

        chapter_title = str(chapter_title).upper().strip()
        anim_style = (config.get("chapter_card_style") or preset.get("chapter_animation", "bracket_frame")).lower().replace(" ", "_")
        pos_anchor = (config.get("chapter_card_position") or preset.get("chapter_card_position", "center")).lower().replace(" ", "_")

        bg_rgba = config.get("chapter_card_bg_color", preset.get("chapter_card_bg_color", (0, 0, 0, 180)))
        accent_color = config.get("chapter_card_accent_color", preset.get("chapter_card_accent_color", (68, 136, 255)))

        font_size = max(20, int(h * 0.065))
        font = get_cached_font(config.get("font", preset.get("font", "DejaVuSans-Bold.ttf")), font_size)

        base_pil = Image.fromarray(frame).convert("RGBA")
        overlay_pil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay_pil)

        tw, th = measure_text_with_spacing(draw, chapter_title, font, 2)
        card_w = tw + 70
        card_h = th + 36

        if pos_anchor == "upper_third":
            target_y = int(h * 0.25) - (card_h // 2)
        elif pos_anchor == "lower_third":
            target_y = int(h * 0.75) - (card_h // 2)
        else:
            target_y = int(h * 0.50) - (card_h // 2)

        target_x = (w - card_w) // 2

        # Progress ratio
        p_in = ease_out_back(clamp(t / 0.4))
        p_out = 1.0 if t <= 2.1 else clamp(1.0 - (t - 2.1) / 0.4)
        alpha_scale = p_out
        if alpha_scale <= 0:
            return frame

        eff_bg = (bg_rgba[0], bg_rgba[1], bg_rgba[2], int((bg_rgba[3] if len(bg_rgba) > 3 else 180) * alpha_scale))
        eff_accent = (accent_color[0], accent_color[1], accent_color[2], int(255 * alpha_scale))

        if anim_style == "bracket_frame":
            # Two accent brackets [ ] slide in from left/right and frame title
            b_off = int(60 * (1.0 - p_in))
            draw.rounded_rectangle([target_x, target_y, target_x + card_w, target_y + card_h], radius=12, fill=eff_bg)

            # Left Bracket [
            draw.line([(target_x - b_off + 10, target_y + 6), (target_x - b_off + 10, target_y + card_h - 6)], fill=eff_accent, width=4)
            draw.line([(target_x - b_off + 10, target_y + 6), (target_x - b_off + 24, target_y + 6)], fill=eff_accent, width=4)
            draw.line([(target_x - b_off + 10, target_y + card_h - 6), (target_x - b_off + 24, target_y + card_h - 6)], fill=eff_accent, width=4)

            # Right Bracket ]
            draw.line([(target_x + card_w + b_off - 10, target_y + 6), (target_x + card_w + b_off - 10, target_y + card_h - 6)], fill=eff_accent, width=4)
            draw.line([(target_x + card_w + b_off - 24, target_y + 6), (target_x + card_w + b_off - 10, target_y + 6)], fill=eff_accent, width=4)
            draw.line([(target_x + card_w + b_off - 24, target_y + card_h - 6), (target_x + card_w + b_off - 10, target_y + card_h - 6)], fill=eff_accent, width=4)

            draw_text_with_spacing(draw, (target_x + 35, target_y + 18), chapter_title, font, (255, 255, 255, int(255 * alpha_scale)), 2)

        elif anim_style == "underline_draw":
            # Accent line draws left-to-right beneath text
            line_w = int(card_w * clamp(p_in * 1.3))
            draw.rounded_rectangle([target_x, target_y, target_x + card_w, target_y + card_h], radius=12, fill=eff_bg)
            draw.line([(target_x + 15, target_y + card_h - 4), (target_x + 15 + line_w, target_y + card_h - 4)], fill=eff_accent, width=4)
            draw_text_with_spacing(draw, (target_x + 35, target_y + 16), chapter_title, font, (255, 255, 255, int(255 * alpha_scale)), 2)

        else:  # slide_horizontal (Default)
            draw_x = int(-card_w + (target_x + card_w) * p_in)
            draw.rounded_rectangle([draw_x, target_y, draw_x + card_w, target_y + card_h], radius=12, fill=eff_bg, outline=eff_accent, width=2)
            draw_text_with_spacing(draw, (draw_x + 35, target_y + 18), chapter_title, font, (255, 255, 255, int(255 * alpha_scale)), 2)

        final_pil = Image.alpha_composite(base_pil, overlay_pil).convert("RGB")
        return np.array(final_pil)

    except Exception:
        return frame


# ── 7. ADVANCED OUTRO CTA OVERLAY ─────────────────────────────────────────────
def apply_outro_overlay(frame: np.ndarray, t: float, scene_duration: float, outro_data: dict, config: dict) -> np.ndarray:
    """
    Draws Outro CTA overlay with sweeping Gradient Pulse Border and pulsing Subscribe button over real video frame.
    """
    outro_dur = float(config.get("outro_duration", 4.0))
    start_t = max(0.0, scene_duration - outro_dur)
    if t < start_t:
        return frame

    try:
        h, w = frame.shape[:2]
        rel_t = t - start_t
        p_fade = clamp(rel_t / 0.4)
        alpha = int(255 * p_fade)

        preset = get_overlay_preset(config.get("overlay_preset", "🎬 Cinematic Warm"))
        outro_data = outro_data or {}

        thanks_text = str(config.get("outro_thanks_text") or outro_data.get("thanks_text") or "THANKS FOR WATCHING!").upper().strip()
        cta_text = str(config.get("outro_cta_override") or outro_data.get("cta_text") or "LIKE & SUBSCRIBE FOR MORE").upper().strip()
        channel_name = str(config.get("outro_channel_name") or "@YourChannel").strip()

        accent_color = config.get("outro_accent_color", preset.get("outro_accent_color", (255, 0, 0)))
        if isinstance(accent_color, str) and accent_color.startswith("#"):
            accent_color = hex_to_rgb(accent_color)

        font_thanks_size = max(24, int(h * 0.070))
        font_cta_size = max(18, int(h * 0.045))
        font_channel_size = max(16, int(h * 0.040))
        font_btn_size = max(16, int(h * 0.038))

        font_thanks = get_cached_font(config.get("font", preset.get("font", "DejaVuSans-Bold.ttf")), font_thanks_size)
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
        if config.get("outro_show_subscribe", True):
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
        if config.get("outro_show_like", True):
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
