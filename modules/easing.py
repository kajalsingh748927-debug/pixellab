"""
modules/easing.py
─────────────────────────────────────────────────────────────────────────────
Shared Easing & Motion Curves Library for Pixelab.

Provides standard motion curves for cinematic title card animations:
  • ease_out_back     — Smooth deceleration with a subtle elastic overshoot
  • ease_in_out_expo  — High-contrast exponential ease-in-out curve
  • spring_overshoot  — Physical spring bounce curve
  • ease_out_quad     — Smooth quadratic deceleration
  • clamp             — Helper to constrain progress between 0.0 and 1.0
─────────────────────────────────────────────────────────────────────────────
"""
import math


def clamp(val: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    return min(max(val, min_val), max_val)


def ease_out_quad(t: float) -> float:
    t = clamp(t)
    return 1.0 - (1.0 - t) * (1.0 - t)


def ease_out_back(t: float, s: float = 1.70158) -> float:
    t = clamp(t)
    t = t - 1.0
    return 1.0 + (t * t * ((s + 1.0) * t + s))


def ease_in_out_expo(t: float) -> float:
    t = clamp(t)
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    if t < 0.5:
        return math.pow(2, 20 * t - 10) / 2.0
    return (2.0 - math.pow(2, -20 * t + 10)) / 2.0


def spring_overshoot(t: float, frequency: float = 12.0, decay: float = 5.0) -> float:
    t = clamp(t)
    if t >= 1.0:
        return 1.0
    return 1.0 - math.exp(-decay * t) * math.cos(frequency * t)
