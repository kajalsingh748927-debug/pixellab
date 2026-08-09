"""
modules/cinematic_packages.py
─────────────────────────────────────────────────────────────────────────────
Cinematic Master Bundles Engine for Pixelab — Upgraded Realistic Presets.

Provides Industry-Standard All-in-One Cinematic Master Bundles with
3-Way Lift/Gamma/Gain Color Science, Skin Protection, and Scalable Intensity Tiers:
  1. 🎬 Hollywood Blockbuster
  2. 🔥 Cyberpunk Neon
  3. ☀️ Golden Hour Magic
  4. 🌾 Vintage 70s Film
  5. 🕶️ Moody Film Noir
  6. 👑 Dark Luxury Gold
  7. 🚀 Action Thriller Dynamic
  8. 🧘 Minimalist Clean Documentary
  9. 🖤 High Contrast Monochrome
 10. ❄️ Nordic Muted (New)
 11. 🎙️ Interview Clean (New)
 12. 🎖️ War Documentary (New)
 13. 📼 Retro VHS (New)
 14. 🌌 IMAX Neutral (New)

Usage:
    from modules.cinematic_packages import get_cinematic_package, CINEMATIC_PACKAGES
    pkg = get_cinematic_package("🎬 Hollywood Blockbuster", intensity_tier="Standard")
─────────────────────────────────────────────────────────────────────────────
"""

CINEMATIC_PACKAGES = {
    "🎬 Hollywood Blockbuster": {
        "description": "Teal & Orange 3-way primary grade, cyan/orange split toning, warm halation, and anamorphic flare.",
        "lift": (-5, 2, 8),
        "gamma": (0.95, 1.0, 1.05),
        "gain": (1.10, 1.05, 0.92),
        "saturation": 1.18,
        "wb_strength": 0.65,
        "skin_protect": 0.60,
        "rolloff_knee": 0.75,
        "bloom_intensity": 0.25,
        "enable_bloom": True,
        "enable_anamorphic_flare": True,
        "enable_split_toning": True,
        "split_toning_intensity": 0.20,
        "grain_intensity": 0.06,
        "vignette": 0.35,
        "aberration_px": 2,
        "adaptive": True,
    },

    "🔥 Cyberpunk Neon": {
        "description": "Vibrant electric blues & magentas, deep shadows, chromatic aberration, and neon halation.",
        "lift": (-12, -4, 10),
        "gamma": (0.90, 0.95, 1.15),
        "gain": (0.95, 1.10, 1.30),
        "saturation": 1.50,
        "wb_strength": 0.50,
        "skin_protect": 0.45,
        "rolloff_knee": 0.70,
        "bloom_intensity": 0.40,
        "enable_bloom": True,
        "enable_chromatic_aberration": True,
        "aberration_px": 4,
        "enable_split_toning": True,
        "split_toning_intensity": 0.35,
        "grain_intensity": 0.08,
        "vignette": 0.50,
        "adaptive": True,
    },

    "☀️ Golden Hour Magic": {
        "description": "Warm sun-drenched amber glow, soft highlight rolloff, warm halation, and gentle film grain.",
        "lift": (8, 4, -4),
        "gamma": (1.05, 1.02, 0.92),
        "gain": (1.20, 1.10, 0.88),
        "saturation": 1.22,
        "wb_strength": 0.55,
        "skin_protect": 0.65,
        "rolloff_knee": 0.80,
        "bloom_intensity": 0.35,
        "enable_bloom": True,
        "grain_intensity": 0.12,
        "vignette": 0.25,
        "aberration_px": 1,
        "adaptive": True,
    },

    "🌾 Vintage 70s Film": {
        "description": "Classic retro film stock, warm faded shadows, projector gate weave, and film grain.",
        "lift": (12, 8, 4),
        "gamma": (1.02, 0.98, 0.90),
        "gain": (1.05, 0.98, 0.85),
        "saturation": 0.85,
        "wb_strength": 0.60,
        "skin_protect": 0.70,
        "rolloff_knee": 0.72,
        "grain_intensity": 0.25,
        "enable_gate_weave": True,
        "vignette": 0.45,
        "aberration_px": 2,
        "adaptive": True,
    },

    "🕶️ Moody Film Noir": {
        "description": "Dramatic high contrast, deep crushed shadows, heavy vignette, and shadow-weighted grain.",
        "lift": (-18, -18, -15),
        "gamma": (0.85, 0.85, 0.88),
        "gain": (1.25, 1.25, 1.20),
        "saturation": 0.65,
        "wb_strength": 0.70,
        "skin_protect": 0.50,
        "rolloff_knee": 0.68,
        "grain_intensity": 0.18,
        "vignette": 0.65,
        "aberration_px": 2,
        "adaptive": True,
    },

    "👑 Dark Luxury Gold": {
        "description": "Rich dark aesthetic with glowing gold highlights, sleek lens flares, and soft halation.",
        "lift": (-14, -8, 2),
        "gamma": (0.92, 0.95, 0.98),
        "gain": (1.25, 1.12, 0.85),
        "saturation": 1.20,
        "wb_strength": 0.60,
        "skin_protect": 0.65,
        "rolloff_knee": 0.75,
        "bloom_intensity": 0.35,
        "enable_bloom": True,
        "enable_anamorphic_flare": True,
        "vignette": 0.55,
        "aberration_px": 2,
        "adaptive": True,
    },

    "🚀 Action Thriller Dynamic": {
        "description": "High saturation, punchy contrast, chromatic aberration, and dynamic motion blur.",
        "lift": (-6, -4, 2),
        "gamma": (0.88, 0.92, 0.98),
        "gain": (1.30, 1.25, 1.15),
        "saturation": 1.38,
        "wb_strength": 0.70,
        "skin_protect": 0.55,
        "rolloff_knee": 0.72,
        "enable_chromatic_aberration": True,
        "aberration_px": 3,
        "grain_intensity": 0.08,
        "vignette": 0.30,
        "adaptive": True,
    },

    "🧘 Minimalist Clean Documentary": {
        "description": "Natural neutral colors, high source normalization, skin protection, and clean clarity.",
        "lift": (0, 0, 0),
        "gamma": (1.0, 1.0, 1.0),
        "gain": (1.05, 1.05, 1.05),
        "saturation": 1.00,
        "wb_strength": 0.80,
        "skin_protect": 0.75,
        "rolloff_knee": 0.82,
        "grain_intensity": 0.04,
        "vignette": 0.15,
        "aberration_px": 0,
        "adaptive": True,
    },

    "🖤 High Contrast Monochrome": {
        "description": "Stunning black and white film look with intense contrast and heavy film grain.",
        "lift": (-15, -15, -15),
        "gamma": (0.85, 0.85, 0.85),
        "gain": (1.40, 1.40, 1.40),
        "saturation": 0.00,
        "wb_strength": 0.75,
        "skin_protect": 0.00,
        "rolloff_knee": 0.70,
        "grain_intensity": 0.22,
        "vignette": 0.50,
        "aberration_px": 0,
        "adaptive": True,
    },

    "❄️ Nordic Muted": {
        "description": "Desaturated cool tones, lifted shadows, low contrast, perfect for calm/minimalist content.",
        "lift": (6, 8, 12),
        "gamma": (1.02, 1.04, 1.06),
        "gain": (0.90, 0.92, 0.95),
        "saturation": 0.75,
        "wb_strength": 0.75,
        "skin_protect": 0.70,
        "rolloff_knee": 0.80,
        "grain_intensity": 0.06,
        "vignette": 0.20,
        "aberration_px": 1,
        "adaptive": True,
    },

    "🎙️ Interview Clean": {
        "description": "Neutral colors, maximum skin protection, zero distortion, perfect for talking-head videos.",
        "lift": (0, 0, 0),
        "gamma": (1.0, 1.0, 1.0),
        "gain": (1.02, 1.02, 1.02),
        "saturation": 1.00,
        "wb_strength": 0.85,
        "skin_protect": 0.85,
        "rolloff_knee": 0.85,
        "grain_intensity": 0.02,
        "vignette": 0.12,
        "aberration_px": 0,
        "adaptive": True,
    },

    "🎖️ War Documentary": {
        "description": "Heavy desaturation, cold dark shadows, filmic highlight rolloff, and deep grain.",
        "lift": (-8, -6, -2),
        "gamma": (0.90, 0.92, 0.95),
        "gain": (0.95, 0.92, 0.88),
        "saturation": 0.60,
        "wb_strength": 0.75,
        "skin_protect": 0.65,
        "rolloff_knee": 0.68,
        "grain_intensity": 0.20,
        "vignette": 0.45,
        "aberration_px": 2,
        "adaptive": True,
    },

    "📼 Retro VHS": {
        "description": "Soft highlight clip, slight chroma bleed, nostalgic scan-line feel, and vintage grain.",
        "lift": (10, 5, 12),
        "gamma": (1.05, 0.98, 1.05),
        "gain": (0.98, 0.95, 1.05),
        "saturation": 1.15,
        "wb_strength": 0.50,
        "skin_protect": 0.60,
        "rolloff_knee": 0.70,
        "enable_chromatic_aberration": True,
        "aberration_px": 4,
        "grain_intensity": 0.24,
        "vignette": 0.40,
        "adaptive": True,
    },

    "🌌 IMAX Neutral": {
        "description": "Near-neutral high dynamic range style, crisp resolution, minimal optical stylization.",
        "lift": (-2, -2, -2),
        "gamma": (1.0, 1.0, 1.0),
        "gain": (1.08, 1.08, 1.08),
        "saturation": 1.05,
        "wb_strength": 0.80,
        "skin_protect": 0.70,
        "rolloff_knee": 0.88,
        "grain_intensity": 0.03,
        "vignette": 0.10,
        "aberration_px": 0,
        "adaptive": True,
    },
}


INTENSITY_TIERS = {
    "Subtle": 0.60,
    "Standard": 1.00,
    "Bold": 1.40,
}


def get_cinematic_package(package_name: str, intensity_tier: str = "Standard") -> dict:
    """
    Returns the complete configuration dictionary for a given cinematic package name and intensity tier.
    Scales bloom, flare, grain, vignette, and aberration parameters by the intensity multiplier.
    """
    base_name = package_name if package_name in CINEMATIC_PACKAGES else "🎬 Hollywood Blockbuster"
    pkg = dict(CINEMATIC_PACKAGES[base_name])

    mult = INTENSITY_TIERS.get(intensity_tier, 1.00)
    if mult != 1.00:
        for key in ("bloom_intensity", "grain_intensity", "vignette", "split_toning_intensity"):
            if key in pkg:
                pkg[key] = round(pkg[key] * mult, 3)
        if "aberration_px" in pkg:
            pkg["aberration_px"] = max(0, int(pkg["aberration_px"] * mult))

    pkg["package_name"] = base_name
    pkg["intensity_tier"] = intensity_tier
    return pkg
