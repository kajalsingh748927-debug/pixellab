import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from modules.pro_vfx import apply_pro_vfx_pipeline
from modules.subtitle_packages import get_subtitle_package, SUBTITLE_PACKAGES

# ── EMOJI AUTO-MAPPING ──────────────────────────────────────
EMOJI_MAP = {
    "fire": "🔥", "flame": "🔥", "hot": "🔥", "burn": "🔥",
    "rocket": "🚀", "space": "🚀", "moon": "🚀", "launch": "🚀", "star": "🌟",
    "money": "💰", "cash": "💰", "dollar": "💰", "rich": "💰", "business": "💰",
    "robot": "🤖", "ai": "🤖", "tech": "🤖", "cyber": "🤖", "futuristic": "🔮",
    "city": "🏙️", "train": "🚄", "building": "🏙️", "urban": "🏙️",
    "world": "🌍", "earth": "🌍", "global": "🌍", "human": "👤",
    "speed": "⚡", "fast": "⚡", "energy": "⚡", "solar": "☀️", "power": "⚡",
    "heart": "❤️", "love": "❤️", "idea": "💡", "think": "💡", "brain": "🧠",
    "win": "🏆", "winner": "🏆", "trophy": "🏆", "goal": "🎯", "target": "🎯",
}

def get_word_emoji(word):
    clean = "".join(c for c in word.lower() if c.isalnum())
    return EMOJI_MAP.get(clean, "")


# ── COLOR GRADE PRESETS ─────────────────────────────────────
def apply_color_grade(frame, config):
    grade = config.get("color_grade", "None")
    sat   = config.get("saturation", 1.0)
    alpha = config.get("contrast", 1.05)
    beta  = config.get("brightness", 2)

    # Base brightness/contrast
    frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    # Saturation via HSV
    if sat != 1.0:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * sat, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    # Grade presets
    if grade == "Cinematic Teal & Orange":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.1 + 10, 0, 255).astype(np.uint8)
        g = np.clip(lut * 0.95, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.85, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Warm Sunset":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.15 + 15, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.80, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Cold Blue Steel":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 0.82, 0, 255).astype(np.uint8)
        b = np.clip(lut * 1.20 + 10, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "Vintage Film":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.08 + 8, 0, 255).astype(np.uint8)
        g = np.clip(lut * 1.02 + 5, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.78 + 20, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    elif grade == "High Contrast B&W":
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.convertScaleAbs(gray, alpha=1.3, beta=-20)
        frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif grade == "Moody Dark":
        frame = cv2.convertScaleAbs(frame, alpha=0.80, beta=-15)

    elif grade == "Vibrant Pop":
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.5, 0, 255)
        frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=5)

    elif grade == "Golden Hour":
        lut = np.arange(256, dtype=np.float32)
        r = np.clip(lut * 1.20 + 20, 0, 255).astype(np.uint8)
        g = np.clip(lut * 1.05 + 5, 0, 255).astype(np.uint8)
        b = np.clip(lut * 0.70, 0, 255).astype(np.uint8)
        frame[:, :, 0] = cv2.LUT(frame[:, :, 0], r)
        frame[:, :, 1] = cv2.LUT(frame[:, :, 1], g)
        frame[:, :, 2] = cv2.LUT(frame[:, :, 2], b)

    return frame


# ── VIGNETTE ───────────────────────────────────────────────
def apply_vignette(frame, strength):
    if strength <= 0:
        return frame
    h, w = frame.shape[:2]
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
    mask = 1 - np.clip(dist * strength, 0, 1)
    mask = mask[:, :, np.newaxis]
    return np.clip(frame * mask, 0, 255).astype(np.uint8)


# ── FILM GRAIN ─────────────────────────────────────────────
def apply_grain(frame, intensity):
    if intensity <= 0:
        return frame
    noise = np.random.normal(0, intensity * 25, frame.shape).astype(np.int16)
    return np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)


# ── CINEMATIC TRANSITIONS & OVERLAYS ─────────────────────────
def apply_whip_zoom(frame, t, duration, fade_dur=0.30):
    """Whip Zoom motion blur on scene entrance."""
    if t < fade_dur:
        progress = 1.0 - (t / fade_dur)
        scale = 1.0 + 0.16 * progress
        h, w = frame.shape[:2]
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (nw, nh))
        dx, dy = (nw - w) // 2, (nh - h) // 2
        crop = resized[max(0, dy):max(0, dy)+h, max(0, dx):max(0, dx)+w]
        if crop.shape[:2] != (h, w):
            crop = cv2.resize(crop, (w, h))
        blur_k = max(1, int(15 * progress)) | 1
        return cv2.GaussianBlur(crop, (blur_k, blur_k), 0)
    return frame

def apply_glitch_vfx(frame, t, duration, glitch_dur=0.25):
    """RGB split digital glitch effect on scene entrance."""
    if t < glitch_dur:
        shift = max(1, int(16 * (1.0 - t / glitch_dur)))
        h, w = frame.shape[:2]
        glitch = frame.copy()
        glitch[:, shift:, 0] = frame[:, :-shift, 0]  # Red channel shift
        glitch[:, :-shift, 2] = frame[:, shift:, 2]  # Blue channel shift
        return glitch
    return frame

def apply_light_leak(frame, t, duration):
    """Anamorphic optical lens flare & warm light leak overlay."""
    progress = t / max(duration, 0.1)
    if 0.10 < progress < 0.50:
        alpha = np.sin(np.pi * (progress - 0.10) / 0.40) * 0.28
        h, w = frame.shape[:2]
        flare = np.zeros((h, w, 3), dtype=np.float32)
        Y, X = np.ogrid[:h, :w]
        dist = np.sqrt(((X - w * 0.85) / w) ** 2 + ((Y - h * 0.15) / h) ** 2)
        flare[:, :, 0] = np.clip(1.0 - dist * 1.4, 0, 1) * 255  # Red
        flare[:, :, 1] = np.clip(1.0 - dist * 1.8, 0, 1) * 170  # Green
        flare[:, :, 2] = np.clip(1.0 - dist * 2.5, 0, 1) * 50   # Blue
        return cv2.addWeighted(frame, 1.0, flare.astype(np.uint8), alpha, 0)
    return frame


# ── LETTERBOX ──────────────────────────────────────────────
def apply_letterbox(frame, ratio_str):
    h, w = frame.shape[:2]
    ratio_map = {
        "2.35:1 (Anamorphic)": 2.35,
        "2.39:1 (Ultra Scope)": 2.39,
        "1.85:1 (Flat)": 1.85,
    }
    ratio = ratio_map.get(ratio_str, 2.35)
    bar_h = int((h - (w / ratio)) / 2)
    if bar_h > 0:
        frame[:bar_h, :] = 0
        frame[h - bar_h:, :] = 0
    return frame


# ── SUBTITLE COLOR STYLES ──────────────────────────────────
SUBTITLE_STYLES = {
    "Kinetic Yellow":   {"active": (255, 235, 59),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Cyberpunk Neon":   {"active": (0, 255, 255),   "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": (255, 0, 128)},
    "Clean Classic":    {"active": (255, 255, 255),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Boxed Background": {"active": (255, 235, 59),   "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Fire Red":         {"active": (255, 60, 30),    "inactive": (255, 220, 200), "stroke": (80, 0, 0),      "stroke_active": None},
    "Instagram White":  {"active": (255, 255, 255),  "inactive": (200, 200, 200), "stroke": (0, 0, 0),       "stroke_active": None},
    "MrBeast Bold":     {"active": (255, 220, 0),    "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": (200, 0, 0)},
    "Gradient Rainbow": {"active": (255, 100, 255),  "inactive": (255, 255, 255), "stroke": (0, 0, 0),       "stroke_active": None},
    "Minimal Fade":     {"active": (255, 255, 255),  "inactive": (180, 180, 180), "stroke": (30, 30, 30),    "stroke_active": None},
}

FONT_MAP = {
    "💥 Impact (Heavy Viral Bold)": "C:/Windows/Fonts/impact.ttf",
    "🅰️ Arial Black (Modern Bold)": "C:/Windows/Fonts/arialbd.ttf",
    "⚡ Trebuchet (Kinetic Dynamic)": "C:/Windows/Fonts/trebucbd.ttf",
    "📖 Georgia (Cinematic Serif)": "C:/Windows/Fonts/georgiab.ttf",
    "🗯️ Comic Sans (Fun & Casual)": "C:/Windows/Fonts/comicbd.ttf",
    "🖥️ Courier New (Retro Monospace)": "C:/Windows/Fonts/courbd.ttf",
    "📜 Times New Roman (Classic)": "C:/Windows/Fonts/timesbd.ttf",
    "✨ Verdana (Clean Ultra-Readable)": "C:/Windows/Fonts/verdanab.ttf",
    "🔹 Tahoma (Crisp Tech)": "C:/Windows/Fonts/tahomabd.ttf",
    "📱 Segoe UI (Modern UI)": "C:/Windows/Fonts/segoeuib.ttf",
    "🍿 DejaVu Sans Bold (Default)": "DejaVuSans-Bold.ttf",
    "DejaVuSans-Bold.ttf": "DejaVuSans-Bold.ttf",
}

def resolve_font_path(font_name: str) -> str:
    if font_name in FONT_MAP and os.path.exists(FONT_MAP[font_name]):
        return FONT_MAP[font_name]
    if os.path.exists(font_name):
        return font_name
    return "DejaVuSans-Bold.ttf"

SIZE_MAP = {
    "Tiny": 0.025, "Small": 0.038, "Medium": 0.055,
    "Large": 0.072, "Extra Large": 0.090, "Massive": 0.115
}

POS_MAP = {
    "Bottom": 0.83, "Lower Center": 0.72, "Center": 0.47,
    "Upper Center": 0.28, "Top": 0.10
}


def draw_kinetic_subtitles(frame, text, t, duration, config, word_timestamps=None):
    """
    Renders kinetic word-by-word highlighted subtitles directly on top of frame.
    Supports ElevenLabs/Whisper millisecond timestamps or linear fallback.
    """
    if not text or not text.strip():
        return frame

    h, w = frame.shape[:2]
    all_words = [w_str for w_str in text.split() if w_str]
    if not all_words:
        return frame

    # 1. Determine active word index from word timestamps or time ratio
    global_active_idx = 0
    if word_timestamps and len(word_timestamps) > 0:
        for idx, wt in enumerate(word_timestamps):
            if wt["start"] <= t <= wt["end"]:
                global_active_idx = idx
                break
            elif t > wt["end"]:
                global_active_idx = idx
    else:
        progress = min(max(t / max(duration, 0.1), 0.0), 1.0)
        global_active_idx = min(int(progress * len(all_words)), len(all_words) - 1)

    pkg_name = config.get("subtitle_package", "Custom (Manual Controls)")
    pkg = get_subtitle_package(pkg_name) if pkg_name != "Custom (Manual Controls)" else None

    # Resolve settings from Package or Manual controls
    active_color   = pkg["active_color"] if pkg else SUBTITLE_STYLES.get(config.get("style", "Kinetic Yellow"), SUBTITLE_STYLES["Kinetic Yellow"])["active"]
    inactive_color = pkg["inactive_color"] if pkg else SUBTITLE_STYLES.get(config.get("style", "Kinetic Yellow"), SUBTITLE_STYLES["Kinetic Yellow"])["inactive"]
    stroke_col_def = pkg["stroke_color"] if pkg else SUBTITLE_STYLES.get(config.get("style", "Kinetic Yellow"), SUBTITLE_STYLES["Kinetic Yellow"])["stroke"]
    stroke_active  = pkg["active_stroke_color"] if pkg else SUBTITLE_STYLES.get(config.get("style", "Kinetic Yellow"), SUBTITLE_STYLES["Kinetic Yellow"]).get("stroke_active")
    stroke_r       = pkg["stroke_width"] if pkg else max(3, config.get("stroke_width", 5))
    font_raw       = pkg["font_file"] if pkg else config.get("font", "💥 Impact (Heavy Viral Bold)")
    font_file      = resolve_font_path(font_raw)
    pos_key        = pkg["position"] if pkg else config.get("position", "Bottom")
    size_key       = pkg["size"] if pkg else config.get("size", "Medium")
    enable_emojis  = pkg["enable_emojis"] if pkg else True

    # Resolve background box — default to None (no black box)
    user_bg_opt = config.get("subtitle_bg_box", "None (Clean Floating Text)")
    if user_bg_opt == "Dark Pill Box":
        box_bg = (0, 0, 0, 180)
        box_border = (255, 255, 255, 100)
    elif user_bg_opt == "Semi-Transparent Shadow":
        box_bg = (0, 0, 0, 110)
        box_border = None
    else:
        box_bg = pkg.get("box_bg") if pkg else None
        box_border = pkg.get("box_border") if pkg else None

    chunk_size = pkg["chunk_size"] if pkg else (4 if len(all_words) > 6 else 3)
    total_words = len(all_words)

    # Chunk words into phrases
    chunks = [all_words[i:i + chunk_size] for i in range(0, total_words, chunk_size)]
    
    current_chunk_idx = global_active_idx // chunk_size
    if current_chunk_idx >= len(chunks):
        current_chunk_idx = len(chunks) - 1

    words = chunks[current_chunk_idx]
    local_active_idx = global_active_idx % chunk_size
    if local_active_idx >= len(words):
        local_active_idx = len(words) - 1

    img  = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    font_size = max(24, int(h * SIZE_MAP.get(size_key, 0.055)))
    try:
        font = ImageFont.truetype(font_file, font_size)
    except IOError:
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()

    start_y = int(h * POS_MAP.get(pos_key, 0.83))

    # Add auto-emojis to active word
    display_words = []
    for i, w_str in enumerate(words):
        emoji = get_word_emoji(w_str) if enable_emojis else ""
        if i == local_active_idx and emoji:
            display_words.append(f"{w_str} {emoji}")
        else:
            display_words.append(w_str)

    total_text = " ".join(display_words)
    bbox = draw.textbbox((0, 0), total_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    alignment = config.get("alignment", "Center")
    if alignment == "Center":
        start_x = max(20, (w - text_w) // 2)
    elif alignment == "Left":
        start_x = 40
    else:
        start_x = max(20, w - text_w - 40)

    # Optional Pill / lower third background box
    if box_bg:
        px, py = 24, 14
        draw.rectangle([
            max(10, start_x - px), start_y - py,
            min(w - 10, start_x + text_w + px), start_y + text_h + py
        ], fill=box_bg, outline=box_border, width=2 if box_border else 0)

    space_w   = draw.textbbox((0, 0), " ", font=font)[2]
    current_x = start_x

    for idx, d_word in enumerate(display_words):
        word_w = draw.textbbox((0, 0), d_word, font=font)[2]
        is_active = (idx == local_active_idx)

        color = active_color if is_active else inactive_color
        stroke_c = stroke_active if (is_active and stroke_active) else stroke_col_def

        # Check if word is an emphasis word or contains numbers (e.g., "180", "KG", "SATURN")
        w_clean_upper = "".join(c for c in d_word.upper() if c.isalnum())
        emph_words = [str(w).upper() for w in config.get("emphasis_words", [])]
        is_emphasis = is_active and (w_clean_upper in emph_words or any(c.isdigit() for c in d_word))

        if is_emphasis:
            color = (255, 235, 59) if (idx % 2 == 0) else (0, 255, 255)
            stroke_c = (0, 0, 0)
            pop_scale = 1.42
        else:
            pop_scale = 1.15 if is_active else 1.0


        # Heavy stroke for maximum contrast over video
        eff_stroke = stroke_r + 2 if is_emphasis else stroke_r
        for sx in range(-eff_stroke, eff_stroke + 1):
            for sy in range(-eff_stroke, eff_stroke + 1):
                if sx != 0 or sy != 0:
                    draw.text((current_x + sx, start_y + sy), d_word, font=font, fill=stroke_c)

        # Scale Pop micro-animation on active word
        if is_active:
            try:
                pop_size = int(font_size * pop_scale)
                pop_font = ImageFont.truetype(font_file, pop_size)
                offset_y = -8 if is_emphasis else -4
                draw.text((current_x - 3, start_y + offset_y), d_word, font=pop_font, fill=color)
            except Exception:
                draw.text((current_x, start_y), d_word, font=font, fill=color)
        else:
            draw.text((current_x, start_y), d_word, font=font, fill=color)

        current_x += word_w + space_w

    return np.array(img.convert("RGB"))



def apply_cinematic_vfx(frame, text, t, duration, config, word_timestamps=None):
    """Master VFX pipeline — runs all effects in order."""

    # 1. Pro Visual FX Pipeline (Auto WB, Primary Grade, Skin Protect, Rolloff, Halation, Grain, etc.)
    has_face = config.get("has_face", False)
    frame = apply_pro_vfx_pipeline(frame, t, config, has_face=has_face)

    # 4. Cinematic Transitions & Overlays
    trans_style = config.get("transition_style", "Whip Zoom & Motion Blur")
    if trans_style == "Whip Zoom & Motion Blur":
        frame = apply_whip_zoom(frame, t, duration)
    elif trans_style == "Glitch RGB Split":
        frame = apply_glitch_vfx(frame, t, duration)
    elif trans_style == "Anamorphic Light Leak":
        frame = apply_light_leak(frame, t, duration)

    # 5. Letterbox
    if config.get("enable_letterbox"):
        frame = apply_letterbox(frame, config.get("letterbox_ratio", "2.35:1 (Anamorphic)"))

    # 6. Kinetic Word Subtitles (ElevenLabs/Whisper timestamp sync or linear fallback)
    frame = draw_kinetic_subtitles(
        frame, text, t, duration, config,
        word_timestamps=word_timestamps
    )

    # 7. AI Fact Card Overlay (Lower-third info callout with 0 -> N Count-Up animation)
    if config.get("enable_fact_cards", True) and config.get("fact_card"):
        frame = draw_fact_card_overlay(frame, config["fact_card"], t=t, duration=duration)

    # 8. AI Map / Location Callout Overlay
    if config.get("map_location"):
        frame = draw_map_location_overlay(frame, config["map_location"])

    return frame


def draw_fact_card_overlay(frame, fact_data, t=0.0, duration=1.0):
    """
    Renders a sleek lower-third glassmorphic Info Badge with dynamic $0 \rightarrow N$
    count-up animation over scene duration.
    """
    if not fact_data or not isinstance(fact_data, dict):
        return frame

    label = str(fact_data.get("label", "KEY FACT")).strip().upper()
    val_raw = str(fact_data.get("value", "")).strip()
    if not val_raw:
        return frame

    # Extract digits for count-up interpolation
    import re
    nums = re.findall(r'\d+', val_raw.replace(',', ''))
    if nums and duration > 0:
        target_num = int(nums[0])
        progress = min(1.0, max(0.0, t / (duration * 0.65)))
        curr_num = int(target_num * progress)
        val = val_raw.replace(nums[0], f"{curr_num:,}")
    else:
        val = val_raw

    h, w = frame.shape[:2]
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    lbl_size = max(13, int(h * 0.020))
    val_size = max(17, int(h * 0.030))

    try:
        font_lbl = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", lbl_size)
        font_val = ImageFont.truetype("C:/Windows/Fonts/impact.ttf", val_size)
    except IOError:
        font_lbl = font_val = ImageFont.load_default()

    lbl_bbox = font_lbl.getbbox(label)
    val_bbox = font_val.getbbox(val)

    card_w = max(lbl_bbox[2] - lbl_bbox[0], val_bbox[2] - val_bbox[0]) + 36
    card_h = (lbl_bbox[3] - lbl_bbox[1]) + (val_bbox[3] - val_bbox[1]) + 26

    margin_x = int(w * 0.05)
    margin_y = int(h * 0.08)

    x1, y1 = margin_x, margin_y
    x2, y2 = x1 + card_w, y1 + card_h

    # Semi-transparent dark pill with cyan accent line
    draw.rounded_rectangle([x1, y1, x2, y2], radius=10, fill=(15, 23, 42, 215), outline=(56, 189, 248, 220), width=2)
    draw.rounded_rectangle([x1 + 4, y1 + 6, x1 + 10, y2 - 6], radius=3, fill=(56, 189, 248, 255))

    tx = x1 + 20
    draw.text((tx, y1 + 8), label, font=font_lbl, fill=(148, 163, 184, 255))
    draw.text((tx, y1 + 12 + (lbl_bbox[3] - lbl_bbox[1])), val, font=font_val, fill=(255, 235, 59, 255))

    return np.array(img)


def draw_map_location_overlay(frame, location_name: str):
    """
    Renders a glowing top-right glassmorphic 3D Location Callout Badge.
    """
    if not location_name:
        return frame

    loc_str = f"📍 LOCATION: {str(location_name).upper().strip()}"
    h, w = frame.shape[:2]
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")

    font_size = max(14, int(h * 0.024))
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    bbox = font.getbbox(loc_str)
    badge_w = (bbox[2] - bbox[0]) + 30
    badge_h = (bbox[3] - bbox[1]) + 18

    x2 = w - int(w * 0.05)
    x1 = x2 - badge_w
    y1 = int(h * 0.08)
    y2 = y1 + badge_h

    draw.rounded_rectangle([x1, y1, x2, y2], radius=8, fill=(15, 23, 42, 220), outline=(245, 158, 11, 230), width=2)
    draw.text((x1 + 15, y1 + 8), loc_str, font=font, fill=(255, 255, 255, 255))

    return np.array(img)




def generate_live_preview_frame(config: dict, sample_text: str = "NEON CITIES ARE EXPANDING TODAY 🔥", active_word_index: int = 2) -> np.ndarray:
    """
    Generates a fast (<10ms) live preview image frame matching the user's current
    sidebar settings (aspect ratio, color grade Preset, brightness, contrast,
    saturation, vignette, typography package, font, size, position, active highlight).
    """
    aspect = config.get("aspect_ratio", "16:9 Landscape (YouTube)")

    if "9:16" in aspect:
        w, h = 540, 960
    elif "1:1" in aspect:
        w, h = 640, 640
    elif "4:3" in aspect:
        w, h = 800, 600
    elif "2.35:1" in aspect:
        w, h = 940, 400
    else:
        w, h = 960, 540

    # 1. Generate stylized synthetic cinematic scene background
    Y, X = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 3
    dist = np.sqrt(((X - cx) / w) ** 2 + ((Y - cy) / h) ** 2)

    # Gradient sky + horizon landscape background
    r_chan = np.clip(30 + 120 * (Y / h) + 40 * (1 - dist), 0, 255).astype(np.uint8)
    g_chan = np.clip(20 + 80 * (Y / h) + 60 * (1 - dist), 0, 255).astype(np.uint8)
    b_chan = np.clip(50 + 160 * (1 - Y / h) + 50 * (1 - dist), 0, 255).astype(np.uint8)
    bg = np.dstack((r_chan, g_chan, b_chan))

    # Add subtle distant city silhouette / horizon line
    horizon_y = int(h * 0.65)
    bg[horizon_y:, :] = (bg[horizon_y:, :] * 0.4).astype(np.uint8)

    # 2. Build mock word timestamps so active_word_index is highlighted
    words = [w for w in sample_text.split() if w]
    n_words = max(len(words), 1)
    dur = 4.0
    time_per_word = dur / n_words
    t_preview = min(active_word_index * time_per_word + 0.1, dur - 0.05)

    word_ts = [
        {
            "word":  w,
            "start": round(i * time_per_word, 3),
            "end":   round((i + 1) * time_per_word, 3),
        }
        for i, w in enumerate(words)
    ]

    # 3. Apply full VFX + Color Grade + Kinetic Subtitles
    preview_frame = apply_cinematic_vfx(
        bg, sample_text, t=t_preview, duration=dur,
        config=config, word_timestamps=word_ts
    )

    return preview_frame