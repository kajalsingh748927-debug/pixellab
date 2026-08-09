"""
modules/pro_vfx.py
─────────────────────────────────────────────────────────────────────────────
Hollywood & Commercial-Grade Pro VFX & Realistic Color Science Engine for Pixelab.

Pipeline Stages:
  1. Auto White Balance Normalization  (normalize_white_balance)
  2. Primary Grade — Lift/Gamma/Gain   (apply_primary_grade)
  3. Skin-Protected Saturation         (apply_skin_protected_saturation)
  4. Filmic Highlight Rolloff           (apply_highlight_rolloff)
  5. Color Halation Glow               (apply_halation)
  6. Anamorphic Lens Flare              (apply_anamorphic_flare)
  7. Chromatic Aberration               (apply_chromatic_aberration)
  8. Split Toning                       (apply_split_toning)
  9. Animated Luminance-Aware Grain     (apply_film_grain)
 10. Film Gate Weave & Lamp Flicker    (apply_film_gate_weave)
─────────────────────────────────────────────────────────────────────────────
"""
import cv2
import numpy as np


# ── 1. AUTO WHITE BALANCE (Source Normalization) ───────────────
def normalize_white_balance(frame: np.ndarray, strength: float = 0.7) -> np.ndarray:
    """
    Gray-world auto white balance blended at `strength` so the source clip's
    natural color cast is normalized before creative grading.
    """
    if strength <= 0:
        return frame

    result = frame.astype(np.float32)
    avg = [result[:, :, i].mean() for i in range(3)]
    avg_gray = sum(avg) / 3.0
    corrected = result.copy()
    for i in range(3):
        corrected[:, :, i] *= (avg_gray / (avg[i] + 1e-6))
    blended = frame.astype(np.float32) * (1.0 - strength) + corrected * strength
    return np.clip(blended, 0, 255).astype(np.uint8)


# ── 2. PRIMARY GRADE — LIFT / GAMMA / GAIN ──────────────────────
def apply_primary_grade(
    frame: np.ndarray,
    lift: tuple = (0, 0, 0),
    gamma: tuple = (1.0, 1.0, 1.0),
    gain: tuple = (1.0, 1.0, 1.0),
) -> np.ndarray:
    """
    3-way primary color correction:
      lift:  per-channel shadow offset (-30..+30)
      gamma: per-channel midtone power (0.7..1.3)
      gain:  per-channel highlight scale (0.7..1.3)
    """
    img = frame.astype(np.float32) / 255.0
    for i in range(3):
        img[:, :, i] = img[:, :, i] * gain[i]
        img[:, :, i] = img[:, :, i] + (lift[i] / 255.0) * (1.0 - img[:, :, i])
        img[:, :, i] = np.power(np.clip(img[:, :, i], 0.0, 1.0), 1.0 / max(0.01, gamma[i]))
    return np.clip(img * 255.0, 0, 255).astype(np.uint8)


# ── 3. SKIN-PROTECTED SATURATION ──────────────────────────────
def apply_skin_protected_saturation(
    frame: np.ndarray,
    saturation: float = 1.25,
    skin_protect: float = 0.60,
) -> np.ndarray:
    """
    Isolates human skin hue band (hue 5-15 in OpenCV HSV 0-179 range)
    and dampens global saturation pushes to prevent orange/sunburnt skin.
    """
    if abs(saturation - 1.0) < 0.01:
        return frame

    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
    hue = hsv[:, :, 0]
    skin_mask = np.clip(1.0 - np.abs(hue - 8.0) / 10.0, 0.0, 1.0)

    effective_sat = saturation - (saturation - 1.0) * skin_protect * skin_mask
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * effective_sat, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)


# ── 4. HIGHLIGHT ROLLOFF (Soft Filmic Compression) ───────────
def apply_highlight_rolloff(
    frame: np.ndarray,
    knee: float = 0.75,
    strength: float = 0.50,
) -> np.ndarray:
    """
    Softly compresses highlights above `knee` instead of hard clipping at 255.
    Gives digital clips an organic, film-like dynamic range.
    """
    img = frame.astype(np.float32) / 255.0
    over = np.clip(img - knee, 0.0, None)
    compressed = knee + over / (1.0 + over * strength * 4.0)
    result = np.where(img > knee, compressed, img)
    return np.clip(result * 255.0, 0, 255).astype(np.uint8)


# ── 5. HALATION (Warm Red/Amber Light Scatter) ────────────────
def apply_halation(
    frame: np.ndarray,
    intensity: float = 0.30,
    threshold: int = 200,
    tint: tuple = (255, 90, 40),
) -> np.ndarray:
    """
    Simulates physical film halation (warm red/orange light scatter around highlights).
    """
    if intensity <= 0:
        return frame

    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    glow = cv2.GaussianBlur(mask, (45, 45), 15).astype(np.float32) / 255.0

    tint_layer = np.zeros_like(frame, dtype=np.float32)
    for i in range(3):
        tint_layer[:, :, i] = glow * tint[i]

    blended = cv2.addWeighted(frame.astype(np.float32), 1.0, tint_layer, intensity, 0)
    return np.clip(blended, 0, 255).astype(np.uint8)


# ── 6. ANIMATED LUMINANCE-AWARE FILM GRAIN ─────────────────────
def apply_film_grain(
    frame: np.ndarray,
    t: float,
    amount: float = 0.08,
    size: float = 1.0,
) -> np.ndarray:
    """
    Temporal noise generator: shadow-weighted, dynamic per frame (using time t).
    """
    if amount <= 0:
        return frame

    h, w = frame.shape[:2]
    seed = int((t * 1000) % 999999)
    rng = np.random.default_rng(seed=seed)
    gh = max(1, int(h / max(0.1, size)))
    gw = max(1, int(w / max(0.1, size)))
    noise = rng.normal(0, 1, (gh, gw)).astype(np.float32)
    noise = cv2.resize(noise, (w, h), interpolation=cv2.INTER_LINEAR)

    luminance = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    shadow_weight = 1.0 - luminance

    grain_layer = noise[:, :, np.newaxis] * amount * 255.0 * shadow_weight[:, :, np.newaxis]
    out = frame.astype(np.float32) + grain_layer
    return np.clip(out, 0, 255).astype(np.uint8)


# ── 7. CONTENT-AWARE ADAPTIVE MODULATION ──────────────────────
def compute_adaptive_modifiers(frame: np.ndarray, has_face: bool = False) -> dict:
    """
    Analyzes frame luma & highlights to dynamically scale bloom, flare, grain, & skin protection.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    mean_luma = gray.mean() / 255.0
    highlight_ratio = (gray > 220).sum() / float(gray.size)

    return {
        "bloom_scale": min(1.0, highlight_ratio * 12.0),
        "flare_scale": min(1.0, highlight_ratio * 8.0),
        "grain_scale": float(np.clip(1.4 - mean_luma, 0.4, 1.6)),
        "skin_protect_scale": 1.4 if has_face else 1.0,
    }


# ── 8. EXISTING OPTICAL EFFECTS ──────────────────────────────
def apply_bloom_glow(frame: np.ndarray, intensity: float = 0.35, threshold: int = 200) -> np.ndarray:
    if intensity <= 0:
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    highlights = cv2.bitwise_and(frame, frame, mask=mask)
    blurred_glow = cv2.GaussianBlur(highlights, (31, 31), 11)
    return cv2.addWeighted(frame, 1.0, blurred_glow, intensity, 0)


def apply_anamorphic_flare(frame: np.ndarray, intensity: float = 0.40) -> np.ndarray:
    if intensity <= 0:
        return frame
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    _, mask = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)
    flare_mask = cv2.GaussianBlur(mask, (1, 51), 0)
    flare_mask = cv2.GaussianBlur(flare_mask, (101, 1), 0)

    flare_color = np.zeros((h, w, 3), dtype=np.uint8)
    flare_color[:, :, 0] = (flare_mask * 0.95).astype(np.uint8)
    flare_color[:, :, 1] = (flare_mask * 0.70).astype(np.uint8)
    flare_color[:, :, 2] = (flare_mask * 0.10).astype(np.uint8)
    return cv2.addWeighted(frame, 1.0, flare_color, intensity, 0)


def apply_chromatic_aberration(frame: np.ndarray, shift_px: int = 3) -> np.ndarray:
    if shift_px <= 0:
        return frame
    h, w = frame.shape[:2]
    r_channel, g_channel, b_channel = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
    mat_r = np.float32([[1, 0, -shift_px], [0, 1, -shift_px]])
    mat_b = np.float32([[1, 0, shift_px], [0, 1, shift_px]])
    r_shifted = cv2.warpAffine(r_channel, mat_r, (w, h), borderMode=cv2.BORDER_REFLECT)
    b_shifted = cv2.warpAffine(b_channel, mat_b, (w, h), borderMode=cv2.BORDER_REFLECT)
    return cv2.merge([r_shifted, g_channel, b_shifted])


def apply_split_toning(
    frame: np.ndarray,
    shadow_color: tuple = (10, 25, 45),
    highlight_color: tuple = (45, 30, 10),
    intensity: float = 0.30,
) -> np.ndarray:
    if intensity <= 0:
        return frame
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255.0
    shadow_mask = np.clip(1.0 - (gray * 2.0), 0.0, 1.0)[:, :, np.newaxis]
    highlight_mask = np.clip((gray - 0.5) * 2.0, 0.0, 1.0)[:, :, np.newaxis]

    s_add = (np.array(shadow_color, dtype=np.float32) * shadow_mask * intensity)
    h_add = (np.array(highlight_color, dtype=np.float32) * highlight_mask * intensity)
    out = frame.astype(np.float32) + h_add - s_add
    return np.clip(out, 0, 255).astype(np.uint8)


def apply_film_gate_weave(frame: np.ndarray, t: float, flicker_freq: float = 8.0) -> np.ndarray:
    h, w = frame.shape[:2]
    dx = int(np.sin(t * 15.0) * 1.5)
    dy = int(np.cos(t * 12.0) * 1.5)
    mat = np.float32([[1, 0, dx], [0, 1, dy]])
    shifted = cv2.warpAffine(frame, mat, (w, h), borderMode=cv2.BORDER_REFLECT)
    flicker = 1.0 + 0.025 * np.sin(t * flicker_freq * 2.0 * np.pi)
    return cv2.convertScaleAbs(shifted, alpha=flicker, beta=0)


# ── MASTER REALISTIC PRO VFX PIPELINE ─────────────────────────
def apply_pro_vfx_pipeline(frame: np.ndarray, t: float, config: dict, has_face: bool = False) -> np.ndarray:
    """
    Master entry point executing the 10-stage realistic grading pipeline.
    """
    # 1. Source Auto White Balance Normalization
    wb_strength = config.get("wb_strength", 0.70)
    frame = normalize_white_balance(frame, strength=wb_strength)

    # 2. Primary 3-Way Grade (Lift / Gamma / Gain)
    lift = config.get("lift", (0, 0, 0))
    gamma = config.get("gamma", (1.0, 1.0, 1.0))
    gain = config.get("gain", (1.0, 1.0, 1.0))
    frame = apply_primary_grade(frame, lift=lift, gamma=gamma, gain=gain)

    # Compute content-aware adaptive modifiers if enabled
    use_adaptive = config.get("adaptive", True)
    mods = compute_adaptive_modifiers(frame, has_face=has_face) if use_adaptive else {
        "bloom_scale": 1.0, "flare_scale": 1.0, "grain_scale": 1.0, "skin_protect_scale": 1.0
    }

    # 3. Skin-Protected Saturation
    sat = config.get("saturation", 1.15)
    skin_prot = config.get("skin_protect", 0.60) * mods["skin_protect_scale"]
    frame = apply_skin_protected_saturation(frame, saturation=sat, skin_protect=skin_prot)

    # 4. Highlight Rolloff
    knee = config.get("rolloff_knee", 0.75)
    frame = apply_highlight_rolloff(frame, knee=knee)

    # 5. Halation Glow
    bloom_intensity = config.get("bloom_intensity", 0.30) * mods["bloom_scale"]
    tint = config.get("halation_tint", (255, 90, 40))
    if bloom_intensity > 0.05:
        frame = apply_halation(frame, intensity=bloom_intensity, tint=tint)

    # 6. Anamorphic Lens Flare
    if config.get("enable_anamorphic_flare", False):
        flare_intensity = 0.35 * mods["flare_scale"]
        frame = apply_anamorphic_flare(frame, intensity=flare_intensity)

    # 7. Chromatic Aberration
    if config.get("enable_chromatic_aberration", False):
        shift_px = config.get("aberration_px", 3)
        frame = apply_chromatic_aberration(frame, shift_px=shift_px)

    # 8. Split Toning
    if config.get("enable_split_toning", False):
        frame = apply_split_toning(frame, intensity=config.get("split_toning_intensity", 0.25))

    # 9. Luminance-Aware Animated Film Grain
    grain_amt = config.get("grain_intensity", 0.0) * mods["grain_scale"]
    if grain_amt > 0.01:
        frame = apply_film_grain(frame, t, amount=grain_amt)

    # 10. Film Gate Weave
    if config.get("enable_gate_weave", False):
        frame = apply_film_gate_weave(frame, t)

    return frame
