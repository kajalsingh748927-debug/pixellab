"""
modules/transitions.py
─────────────────────────────────────────────────────────────────────────────
Cinematic Scene Transitions Library for Pixelab.

Provides 5 high-impact, professional transitions for joining consecutive scenes:
  1. whip_pan          — Fast directional pan with motion blur spike
  2. zoom_blur         — Radial zoom blur with center focal scaling
  3. glitch_rgb_split  — Cyberpunk chromatic aberration & scanline shift
  4. light_leak_wipe   — Warm amber lens flare light leak sweep
  5. speed_ramp        — Slow-down tail snap cut into fast-forward head

Handles any aspect ratio/resolution and preserves audio.
─────────────────────────────────────────────────────────────────────────────
"""
import random
import numpy as np
import cv2
from moviepy import VideoClip, CompositeVideoClip, concatenate_videoclips, vfx

TRANSITION_TYPES = [
    "whip_pan",
    "zoom_blur",
    "glitch_rgb_split",
    "light_leak_wipe",
    "speed_ramp",
]


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="ignore").decode("ascii"))
        except Exception:
            pass


def get_random_transition(exclude: list[str] | None = None) -> str:
    """
    Pick a transition type randomly, excluding specified types to prevent
    consecutive repeating transitions.
    """
    exclude = exclude or []
    choices = [t for t in TRANSITION_TYPES if t not in exclude]
    if not choices:
        choices = TRANSITION_TYPES
    return random.choice(choices)


# ─────────────────────────────────────────────────────────────────────────────
# TRANSITION IMPLEMENTATIONS (NumPy / OpenCV Frame Processors)
# ─────────────────────────────────────────────────────────────────────────────

def _apply_whip_pan(clip_a, clip_b, duration=0.35):
    """Directional horizontal whip pan with motion blur peak at midpoint."""
    w, h = clip_a.size

    def make_frame(t):
        p = min(max(t / max(duration, 0.01), 0.0), 1.0)

        # Retrieve un-blurred frames
        frame_a = clip_a.get_frame(max(0, clip_a.duration - duration + t))
        frame_b = clip_b.get_frame(min(t, clip_b.duration - 0.001))

        # Horizontal pan offset
        shift_x = int(w * p)

        # Motion blur kernel size (peaks at midpoint p=0.5)
        ksize = int(max(1, 49 * np.sin(np.pi * p)))
        if ksize % 2 == 0:
            ksize += 1

        # Composite panned frame
        canvas = np.zeros_like(frame_a)
        if shift_x < w:
            canvas[:, : w - shift_x] = frame_a[:, shift_x:]
        if shift_x > 0:
            canvas[:, w - shift_x :] = frame_b[:, :shift_x]

        # Apply horizontal motion blur filter
        if ksize > 1:
            kernel = np.zeros((1, ksize), dtype=np.float32)
            kernel[0, :] = 1.0 / ksize
            canvas = cv2.filter2D(canvas, -1, kernel)

        return canvas

    return VideoClip(make_frame, duration=duration)


def _apply_zoom_blur(clip_a, clip_b, duration=0.35):
    """Radial zoom blur crossfade."""
    w, h = clip_a.size

    def make_frame(t):
        p = min(max(t / max(duration, 0.01), 0.0), 1.0)
        frame_a = clip_a.get_frame(max(0, clip_a.duration - duration + t))
        frame_b = clip_b.get_frame(min(t, clip_b.duration - 0.001))

        # Scale factor
        scale_a = 1.0 + 0.20 * p
        scale_b = 1.20 - 0.20 * p

        # Zoom A
        nw_a, nh_a = max(1, int(w * scale_a)), max(1, int(h * scale_a))
        res_a = cv2.resize(frame_a, (nw_a, nh_a))
        xa1, ya1 = (nw_a - w) // 2, (nh_a - h) // 2
        crop_a = res_a[ya1 : ya1 + h, xa1 : xa1 + w]

        # Zoom B
        nw_b, nh_b = max(1, int(w * scale_b)), max(1, int(h * scale_b))
        res_b = cv2.resize(frame_b, (nw_b, nh_b))
        xb1, yb1 = (nw_b - w) // 2, (nh_b - h) // 2
        crop_b = res_b[yb1 : yb1 + h, xb1 : xb1 + w]

        # Crossfade blend
        blended = (crop_a.astype(np.float32) * (1.0 - p) + crop_b.astype(np.float32) * p).astype(np.uint8)

        # Radial blur effect at midpoint
        ksize = int(max(1, 25 * np.sin(np.pi * p)))
        if ksize % 2 == 0:
            ksize += 1
        if ksize > 1:
            blended = cv2.GaussianBlur(blended, (ksize, ksize), 0)

        return blended

    return VideoClip(make_frame, duration=duration)


def _apply_glitch_rgb_split(clip_a, clip_b, duration=0.35):
    """Chromatic R/G/B channel shift with scanline displacement glitch."""
    w, h = clip_a.size

    def make_frame(t):
        p = min(max(t / max(duration, 0.01), 0.0), 1.0)
        frame_a = clip_a.get_frame(max(0, clip_a.duration - duration + t))
        frame_b = clip_b.get_frame(min(t, clip_b.duration - 0.001))

        # Base crossfade
        blended = (frame_a.astype(np.float32) * (1.0 - p) + frame_b.astype(np.float32) * p).astype(np.uint8)

        # RGB Split offset
        shift = int(22 * np.sin(np.pi * p))
        if shift > 0:
            res = blended.copy()
            # Red channel shift left
            res[:, :-shift, 0] = blended[:, shift:, 0]
            # Blue channel shift right
            res[:, shift:, 2] = blended[:, :-shift, 2]
            blended = res

        # Scanline displacement near midpoint (0.35 <= p <= 0.65)
        if 0.35 <= p <= 0.65:
            num_glitches = random.randint(2, 4)
            for _ in range(num_glitches):
                y_start = random.randint(0, max(0, h - 30))
                g_height = random.randint(5, 25)
                g_shift = random.randint(-35, 35)
                y_end = min(h, y_start + g_height)
                if g_shift != 0:
                    blended[y_start:y_end] = np.roll(blended[y_start:y_end], g_shift, axis=1)

        return blended

    return VideoClip(make_frame, duration=duration)


def _apply_light_leak_wipe(clip_a, clip_b, duration=0.35):
    """Warm lens flare light leak sweep across crossfaded clips."""
    w, h = clip_a.size
    xx, yy = np.meshgrid(np.linspace(0, 1, w), np.linspace(0, 1, h))

    def make_frame(t):
        p = min(max(t / max(duration, 0.01), 0.0), 1.0)
        frame_a = clip_a.get_frame(max(0, clip_a.duration - duration + t))
        frame_b = clip_b.get_frame(min(t, clip_b.duration - 0.001))

        # Base crossfade
        blended = (frame_a.astype(np.float32) * (1.0 - p) + frame_b.astype(np.float32) * p).astype(np.uint8)

        # Warm amber light leak sweep (top-right to bottom-left gradient)
        center_x = 1.3 - 1.6 * p
        dist = np.sqrt((xx - center_x) ** 2 + (yy - 0.2) ** 2)
        glow = np.clip(1.0 - dist * 1.4, 0, 1) ** 2
        glow_intensity = float(np.sin(np.pi * p))

        light_leak = np.zeros_like(blended)
        light_leak[:, :, 0] = (255 * glow * glow_intensity).astype(np.uint8)  # R
        light_leak[:, :, 1] = (160 * glow * glow_intensity).astype(np.uint8)  # G
        light_leak[:, :, 2] = (50 * glow * glow_intensity).astype(np.uint8)   # B

        res = cv2.addWeighted(blended, 1.0, light_leak, 0.65, 0)
        return res

    return VideoClip(make_frame, duration=duration)


def _apply_speed_ramp(clip_a, clip_b, duration=0.35):
    """
    Speed ramp transition:
    Slow down tail of clip_a to 60% speed, snap-cut into clip_b head at 115% speed.
    """
    ramp_a_dur = min(0.40, clip_a.duration * 0.4)
    ramp_b_dur = min(0.30, clip_b.duration * 0.4)

    head_a = clip_a.subclipped(0, max(0.01, clip_a.duration - ramp_a_dur))
    tail_a = clip_a.subclipped(max(0, clip_a.duration - ramp_a_dur), clip_a.duration)
    tail_a_slow = tail_a.with_effects([vfx.MultiplySpeed(0.60)])

    head_b = clip_b.subclipped(0, min(clip_b.duration, ramp_b_dur))
    head_b_fast = head_b.with_effects([vfx.MultiplySpeed(1.15)])
    tail_b = clip_b.subclipped(min(clip_b.duration, ramp_b_dur), clip_b.duration)

    return concatenate_videoclips([head_a, tail_a_slow, head_b_fast, tail_b])


# ─────────────────────────────────────────────────────────────────────────────
# MASTER TRANSITION APPLICATION ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def apply_transition(
    clip_a,
    clip_b,
    transition_type: str,
    duration: float = 0.35,
) -> VideoClip:
    """
    Blends outgoing `clip_a` into incoming `clip_b` using `transition_type`.
    Returns a single joined MoviePy VideoClip containing the entire un-blended
    portions of both clips plus the transition overlap.
    """
    if clip_a is None or clip_b is None:
        return clip_a or clip_b

    # Graceful degradation if clip is too short
    min_clip_dur = min(clip_a.duration, clip_b.duration)
    if min_clip_dur < (duration + 0.1):
        effective_duration = max(0.10, min_clip_dur * 0.4)
        safe_print(f"⚠️ Clip duration ({min_clip_dur:.2f}s) too short for {duration:.2f}s {transition_type} — degrading to {effective_duration:.2f}s crossfade.")
        return _apply_simple_crossfade(clip_a, clip_b, duration=effective_duration)

    if transition_type == "speed_ramp":
        try:
            return _apply_speed_ramp(clip_a, clip_b, duration=duration)
        except Exception as err:
            safe_print(f"⚠️ Speed ramp transition notice ({err}) — falling back to crossfade.")
            return _apply_simple_crossfade(clip_a, clip_b, duration=duration)

    try:
        head_a = clip_a.subclipped(0, max(0, clip_a.duration - duration))
        tail_b = clip_b.subclipped(min(clip_b.duration, duration), clip_b.duration)

        if transition_type == "whip_pan":
            trans_clip = _apply_whip_pan(clip_a, clip_b, duration=duration)
        elif transition_type == "zoom_blur":
            trans_clip = _apply_zoom_blur(clip_a, clip_b, duration=duration)
        elif transition_type == "glitch_rgb_split":
            trans_clip = _apply_glitch_rgb_split(clip_a, clip_b, duration=duration)
        elif transition_type == "light_leak_wipe":
            trans_clip = _apply_light_leak_wipe(clip_a, clip_b, duration=duration)
        else:
            trans_clip = _apply_simple_crossfade_overlap(clip_a, clip_b, duration=duration)

        parts = [head_a, trans_clip, tail_b]
        valid_parts = [p for p in parts if p is not None and p.duration > 0]
        return concatenate_videoclips(valid_parts)

    except Exception as err:
        safe_print(f"⚠️ Transition error for '{transition_type}' ({err}) — falling back to simple crossfade.")
        return _apply_simple_crossfade(clip_a, clip_b, duration=min(0.20, duration))


def _apply_simple_crossfade_overlap(clip_a, clip_b, duration=0.20):
    w, h = clip_a.size

    def make_frame(t):
        p = min(max(t / max(duration, 0.01), 0.0), 1.0)
        frame_a = clip_a.get_frame(max(0, clip_a.duration - duration + t))
        frame_b = clip_b.get_frame(min(t, clip_b.duration - 0.001))
        return (frame_a.astype(np.float32) * (1.0 - p) + frame_b.astype(np.float32) * p).astype(np.uint8)

    return VideoClip(make_frame, duration=duration)


def _apply_simple_crossfade(clip_a, clip_b, duration=0.15):
    head_a = clip_a.subclipped(0, max(0, clip_a.duration - duration))
    tail_b = clip_b.subclipped(min(clip_b.duration, duration), clip_b.duration)
    trans = _apply_simple_crossfade_overlap(clip_a, clip_b, duration=duration)
    return concatenate_videoclips([head_a, trans, tail_b])
