"""
modules/auto_framing.py
───────────────────────────────────────────────────────────────────────────────
Smart AI Auto-Framing Engine
  • Face & upper-body detection via OpenCV Haar Cascades
  • Temporal box smoothing (EMA) to prevent jitter
  • Letterbox-safe crop centering
  • Graceful fallback to centre-crop when no subject is found
───────────────────────────────────────────────────────────────────────────────
"""

import cv2
import numpy as np

# ── LOAD CLASSIFIERS ONCE ──────────────────────────────────────────────────
def _load_cascade(name):
    path = cv2.data.haarcascades + name
    c = cv2.CascadeClassifier(path)
    if c.empty():
        return None
    return c

_FACE_CASCADE = _load_cascade("haarcascade_frontalface_default.xml")
_BODY_CASCADE = _load_cascade("haarcascade_upperbody.xml")


def _detect_subject_bbox(gray_frame):
    """
    Returns the bounding box (x, y, w, h) of the best detected subject,
    or None if nothing is found.
    Priority: face  >  upper-body.
    """
    if _FACE_CASCADE is not None:
        faces = _FACE_CASCADE.detectMultiScale(
            gray_frame,
            scaleFactor=1.15,
            minNeighbors=4,
            minSize=(40, 40),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(faces):
            # Pick the largest face
            faces = sorted(faces, key=lambda b: b[2] * b[3], reverse=True)
            return faces[0]

    if _BODY_CASCADE is not None:
        bodies = _BODY_CASCADE.detectMultiScale(
            gray_frame,
            scaleFactor=1.10,
            minNeighbors=3,
            minSize=(60, 60),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        if len(bodies):
            bodies = sorted(bodies, key=lambda b: b[2] * b[3], reverse=True)
            return bodies[0]

    return None


class SmartAutoFramer:
    """
    Stateful per-clip framing helper.
    Call .get_crop_x(frame) every frame to get the smoothed left-edge x
    for the portrait crop window.
    """

    def __init__(self, src_w, src_h, dst_w, dst_h, smoothing=0.05):
        """
        src_w/h – dimensions of the incoming stock-footage frame
        dst_w/h – target output resolution (e.g. 1080 × 1920 for portrait)
        smoothing – EMA coefficient (lower = slower / smoother tracking)
        """
        self.src_w = src_w
        self.src_h = src_h
        self.dst_w = dst_w
        self.dst_h = dst_h

        # The crop window maintains the target aspect-ratio at src height
        target_ratio = dst_w / dst_h
        crop_w = int(src_h * target_ratio)
        self.crop_w = min(crop_w, src_w)

        # Default centre crop x
        self._ema_x = float((src_w - self.crop_w) // 2)
        self.smoothing = smoothing
        self._sample_interval = 6   # analyse every N frames (perf)
        self._frame_count = 0

    def _ideal_x_for_subject(self, frame):
        """Returns the ideal crop left-edge x given a detected subject."""
        small = cv2.resize(frame, (frame.shape[1] // 2, frame.shape[0] // 2))
        gray  = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        bbox  = _detect_subject_bbox(gray)
        if bbox is None:
            return None

        # Scale back to full resolution
        bx, by, bw, bh = [v * 2 for v in bbox]
        subject_cx = bx + bw // 2

        # Centre the crop window on the subject
        ideal_x = subject_cx - self.crop_w // 2
        return float(np.clip(ideal_x, 0, self.src_w - self.crop_w))

    def get_crop_x(self, frame):
        """
        Returns the EMA-smoothed left-edge x for cropping this frame.
        Updates internal state every `_sample_interval` frames.
        """
        self._frame_count += 1
        if self._frame_count % self._sample_interval == 0:
            ideal = self._ideal_x_for_subject(frame)
            if ideal is not None:
                # Exponential Moving Average smoothing
                self._ema_x = (1 - self.smoothing) * self._ema_x + self.smoothing * ideal

        return int(np.clip(round(self._ema_x), 0, self.src_w - self.crop_w))

    def crop_frame(self, frame):
        """Crops and resizes one frame using the current tracked position."""
        x1 = self.get_crop_x(frame)
        cropped = frame[:, x1:x1 + self.crop_w]
        if cropped.shape[1] != self.dst_w or cropped.shape[0] != self.dst_h:
            cropped = cv2.resize(cropped, (self.dst_w, self.dst_h))
        return cropped
