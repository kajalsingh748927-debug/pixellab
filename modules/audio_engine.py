"""
modules/audio_engine.py
─────────────────────────────────────────────────────────────────────────────
5-Layer Cinematic Audio Mixing Engine for Pixelab — Vox / Johnny Harris / MagnatesMedia Style.

Implements the 5 Major Audio Layers & Decibel Target Levels:
  1. Track 1: Primary Voice Layer (Voiceover / Interview Anchor) [-6 dB to -12 dB]
  2. Track 2: Real Foley & Hard SFX (Realism & Micro-sounds)      [-10 dB to -18 dB]
  3. Track 3: Cinematic / Emotional SFX (Whooshes, Hits, Risers)  [-12 dB to -20 dB]
  4. Track 4: Environmental & Ambience Layer (Atmosphere)         [-20 dB to -28 dB] (Procedural Atmosphere)
  5. Track 5: Background Music (MX - Underscore Track)            [-20 dB to -30 dB] (Procedural Underscore + Audio Ducking)
─────────────────────────────────────────────────────────────────────────────
"""
import os
import wave
import math
import numpy as np
import requests
from config import OUTPUT_DIR, TEMP_DIR
from moviepy import AudioFileClip, CompositeAudioClip, AudioArrayClip

SFX_DIR = os.path.join(OUTPUT_DIR, "sfx")
os.makedirs(SFX_DIR, exist_ok=True)

def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode('ascii', errors='ignore').decode('ascii'))
        except Exception:
            pass


def generate_elevenlabs_sfx(prompt: str, out_filename: str, duration: float = 1.5) -> bool:
    """Generates custom AI Sound Effects using ElevenLabs Sound Generation API (v1/sound-generation)."""
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not api_key:
        return False
    try:
        url = "https://api.elevenlabs.io/v1/sound-generation"
        headers = {"xi-api-key": api_key}
        payload = {
            "text": prompt,
            "duration_seconds": min(10.0, max(0.5, float(duration))),
            "prompt_influence": 0.5
        }
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(out_filename, "wb") as f:
                f.write(r.content)
            safe_print(f"🔊 [ElevenLabs SFX API] Created '{prompt}' ({len(r.content)} bytes)")
            return True
        else:
            safe_print(f"⚠️ ElevenLabs SFX notice ({r.status_code}): {r.text[:120]}")
    except Exception as e:
        safe_print(f"⚠️ ElevenLabs SFX error: {e}")
    return False


# ─── 0. SOUND SYNTHESIS & ELEVENLABS AI SFX GENERATION ────────────────────

def ensure_sfx_library() -> dict:
    """
    Sound Design Assets Engine (3-tier priority):
      1. Use local file if downloaded/exists (fastest)
      2. Generate custom Sound Effects via ElevenLabs API (v1/sound-generation)
      3. Fall back to high-quality procedural synthesis bed
    """
    fs = 44100
    sfx_map = {}

    # 1. Whoosh SFX (Transition Swish)
    whoosh_path = os.path.join(SFX_DIR, "whoosh.wav")
    if not (os.path.exists(whoosh_path) and os.path.getsize(whoosh_path) > 1000):
        if not generate_elevenlabs_sfx("cinematic whoosh transition swish sound effect", whoosh_path, duration=0.8):
            dur = 0.40
            t = np.linspace(0, dur, int(fs * dur))
            noise = np.random.uniform(-1, 1, len(t))
            envelope = np.sin(np.pi * t / dur) ** 3
            freq_sweep = np.sin(2 * np.pi * (90 + 650 * (t / dur)**2) * t)
            signal = (noise * 0.50 + freq_sweep * 0.50) * envelope
            data = (signal * 32767 * 0.75).astype(np.int16)
            with wave.open(whoosh_path, 'w') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(fs)
                f.writeframes(data.tobytes())
    sfx_map["whoosh"] = whoosh_path

    # 2. Heavy Bass Impact / Thud SFX (Big Reveal / Title Card Drop)
    impact_path = os.path.join(SFX_DIR, "impact.wav")
    if not (os.path.exists(impact_path) and os.path.getsize(impact_path) > 1000):
        if not generate_elevenlabs_sfx("heavy cinematic bass impact thud hit sound effect", impact_path, duration=1.2):
            dur = 0.90
            t = np.linspace(0, dur, int(fs * dur))
            sub_bass = np.sin(2 * np.pi * (140 * np.exp(-t * 8)) * t) # Sub-bass pitch drop from 140Hz to 20Hz
            punch = np.random.uniform(-0.5, 0.5, len(t)) * np.exp(-t * 25)
            signal = (sub_bass * 0.80 + punch * 0.20) * np.exp(-t * 3.5)
            data = (signal * 32767 * 0.85).astype(np.int16)
            with wave.open(impact_path, 'w') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(fs)
                f.writeframes(data.tobytes())
    sfx_map["impact"] = impact_path

    # 3. Cinematic Tension Riser SFX (Slow swell before climax)
    riser_path = os.path.join(SFX_DIR, "riser.wav")
    if not (os.path.exists(riser_path) and os.path.getsize(riser_path) > 1000):
        if not generate_elevenlabs_sfx("cinematic tension swell riser sound effect", riser_path, duration=2.0):
            dur = 1.80
            t = np.linspace(0, dur, int(fs * dur))
            freq_rising = 80 + (t / dur)**2.5 * 800
            swell = (t / dur)**2
            noise_swell = np.random.uniform(-0.4, 0.4, len(t)) * swell
            synth_swell = np.sin(2 * np.pi * freq_rising * t) * swell
            signal = (synth_swell * 0.70 + noise_swell * 0.30)
            data = (signal * 32767 * 0.70).astype(np.int16)
            with wave.open(riser_path, 'w') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(fs)
                f.writeframes(data.tobytes())
    sfx_map["riser"] = riser_path

    # 4. Foley Pop / Card Reveal SFX
    pop_path = os.path.join(SFX_DIR, "pop.wav")
    if not (os.path.exists(pop_path) and os.path.getsize(pop_path) > 1000):
        if not generate_elevenlabs_sfx("subtle UI pop click reveal sound effect", pop_path, duration=0.5):
            dur = 0.08
            t = np.linspace(0, dur, int(fs * dur))
            freq = np.linspace(950, 200, len(t))
            signal = np.sin(2 * np.pi * freq * t) * np.exp(-t * 60)
            data = (signal * 32767 * 0.80).astype(np.int16)
            with wave.open(pop_path, 'w') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(fs)
                f.writeframes(data.tobytes())
    sfx_map["pop"] = pop_path

    # 5. Glitch / Texture SFX
    glitch_path = os.path.join(SFX_DIR, "glitch.wav")
    if not (os.path.exists(glitch_path) and os.path.getsize(glitch_path) > 1000):
        if not generate_elevenlabs_sfx("digital glitch robotic texture sound effect", glitch_path, duration=0.6):
            dur = 0.20
            t = np.linspace(0, dur, int(fs * dur))
            noise = np.random.uniform(-0.8, 0.8, len(t))
            square = np.sign(np.sin(2 * np.pi * 80 * t))
            signal = (noise * 0.5 + square * 0.5) * np.exp(-t * 20)
            data = (signal * 32767 * 0.60).astype(np.int16)
            with wave.open(glitch_path, 'w') as f:
                f.setnchannels(1); f.setsampwidth(2); f.setframerate(fs)
                f.writeframes(data.tobytes())
    sfx_map["glitch"] = glitch_path

    return sfx_map


# ─── PROCEDURAL ATMOSPHERE & BACKGROUND MUSIC GENERATION ────────────────────

def generate_procedural_ambience(visual_context: str, total_duration: float = 30.0) -> str | None:
    """Generates a soft, immersive environmental atmosphere drone bed."""
    amb_file = os.path.join(TEMP_DIR, "environmental_ambience.wav")
    if os.path.exists(amb_file) and os.path.getsize(amb_file) > 10000:
        return amb_file

    try:
        fs = 44100
        dur = max(5.0, float(total_duration))
        t = np.linspace(0, dur, int(fs * dur))

        # Deep warm space/nature atmosphere drone (dual oscillator with lowpass filtering)
        f1, f2 = 55.0, 110.0  # A1 sub-bass drone
        wave1 = np.sin(2 * np.pi * f1 * t + 0.05 * np.sin(2 * np.pi * 0.2 * t))
        wave2 = np.sin(2 * np.pi * f2 * t + 0.08 * np.sin(2 * np.pi * 0.15 * t))
        pink_noise = np.random.uniform(-0.15, 0.15, len(t))

        # Gentle fade in/out
        fade = np.clip(t / 2.0, 0, 1) * np.clip((dur - t) / 2.0, 0, 1)
        signal = (wave1 * 0.50 + wave2 * 0.35 + pink_noise * 0.15) * fade * 0.25

        data = (signal * 32767).astype(np.int16)
        import wave
        with wave.open(amb_file, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(fs)
            f.writeframes(data.tobytes())
        safe_print(f"🌌 Created Procedural Environmental Ambience Track ({dur:.1f}s)")
        return amb_file
    except Exception as e:
        safe_print(f"⚠️ Procedural ambience notice: {e}")
        return None


def fetch_background_music(tone="Cinematic & Epic", visual_context="") -> str | None:
    """Generates an immersive cinematic underscore background music track."""
    music_file = os.path.join(TEMP_DIR, "bg_music.wav")
    if os.path.exists(music_file) and os.path.getsize(music_file) > 10000:
        return music_file

    try:
        fs = 44100
        dur = 45.0
        t = np.linspace(0, dur, int(fs * dur))

        # Warm cinematic chord progression (C minor / G minor cinematic swells)
        base_freqs = [65.41, 77.78, 98.00, 130.81] # C2, Eb2, G2, C3
        chord = np.zeros(len(t))
        for f in base_freqs:
            lfo = 1.0 + 0.05 * np.sin(2 * np.pi * 0.1 * t)
            chord += np.sin(2 * np.pi * f * lfo * t) * 0.20

        sub_pulse = np.sin(2 * np.pi * 32.70 * t) * (0.15 + 0.05 * np.sin(2 * np.pi * 0.5 * t))
        fade = np.clip(t / 3.0, 0, 1) * np.clip((dur - t) / 3.0, 0, 1)
        signal = (chord + sub_pulse) * fade * 0.35

        data = (signal * 32767).astype(np.int16)
        import wave
        with wave.open(music_file, 'w') as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(fs)
            f.writeframes(data.tobytes())
        safe_print(f"🎵 Created Procedural Cinematic Underscore Music Track")
        return music_file
    except Exception as e:
        safe_print(f"⚠️ Procedural music notice: {e}")
        return None


def load_safe_audio_clip(path_or_clip):
    """
    Safely loads any audio file or clip as an AudioArrayClip.
    This prevents MoviePy's AudioFileClip reader from throwing OSErrors
    when sampled beyond file duration inside CompositeAudioClip.
    """
    if path_or_clip is None:
        return None
    if hasattr(path_or_clip, "to_soundarray"):
        try:
            c = path_or_clip
            dur = float(getattr(c, "duration", 0) or 0)
            if dur <= 0:
                return c
            fps = getattr(c, "fps", 44100) or 44100
            times = np.linspace(0, dur, int(fps * dur), endpoint=False)
            arr = c.get_frame(times)
            ac = AudioArrayClip(arr, fps=fps)
            return ac.with_duration(dur)
        except Exception:
            return path_or_clip

    path = str(path_or_clip)
    if not os.path.exists(path):
        return None
    if path.endswith(".wav"):
        try:
            with wave.open(path, "rb") as wf:
                nch = wf.getnchannels()
                sw = wf.getsampwidth()
                rate = wf.getframerate()
                nframes = wf.getnframes()
                raw = wf.readframes(nframes)
                dt = np.int16 if sw == 2 else (np.uint8 if sw == 1 else np.int32)
                arr = np.frombuffer(raw, dtype=dt)
                if nch > 1:
                    arr = arr.reshape(-1, nch)
                else:
                    arr = np.column_stack([arr, arr])
                arr = arr.astype(np.float32) / (32768.0 if sw == 2 else 128.0)
                dur = float(nframes) / float(rate)
                ac = AudioArrayClip(arr, fps=rate)
                return ac.with_duration(dur)
        except Exception:
            pass
    try:
        c = AudioFileClip(path)
        dur = float(getattr(c, "duration", 0) or 0)
        if dur <= 0:
            return c
        fps = getattr(c, "fps", 44100) or 44100
        times = np.linspace(0, dur, int(fps * dur), endpoint=False)
        arr = c.get_frame(times)
        c.close()
        ac = AudioArrayClip(arr, fps=fps)
        return ac.with_duration(dur)
    except Exception:
        return AudioFileClip(path)


# ─── MASTER 5-LAYER AUDIO MIXING PIPELINE ───────────────────────────────────

def mix_master_audio(
    voice_clips: list,
    total_duration: float,
    config: dict,
    master_voiceover_path: str | None = None,
    uploaded_audio_path: str | None = None,
    scenes: list | None = None,
) -> CompositeAudioClip:
    """
    Vox / Johnny Harris / MagnatesMedia 5-Layer Hollywood Audio Mixer:

    Layer Order & Decibel Target Levels:
      • Track 1: Voiceover / Narration Anchor  [-6 dB to -12 dB] (Center Anchor)
      • Track 2: Real Foley & Micro SFX         [-10 dB to -18 dB] (Stats/Facts Reveal)
      • Track 3: Cinematic SFX (Whoosh/Hits)   [-12 dB to -20 dB] (Scene Cuts & Title Drops)
      • Track 4: Environmental Ambience Layer  [-20 dB to -28 dB] (Procedural Atmosphere)
      • Track 5: Background Music (MX)          [-20 dB to -30 dB] (Procedural Underscore + Auto-Ducking)
    """
    sfx_library = ensure_sfx_library()
    audio_layers = []

    # Extract visual context from scenes for sound design matching
    scenes = scenes or []
    all_queries_text = " ".join(sc.get("search_query", "") for sc in scenes if isinstance(sc, dict))

    # ─────────────────────────────────────────────────────────────────────────
    # TRACK 1: Primary Voice Layer (Voiceover & Narration Anchor) [-6 dB to -12 dB]
    # ─────────────────────────────────────────────────────────────────────────
    voice_layer = None
    if uploaded_audio_path and os.path.exists(uploaded_audio_path):
        try:
            v_clip = load_safe_audio_clip(uploaded_audio_path)
            if v_clip and v_clip.duration > total_duration:
                v_clip = v_clip.subclipped(0, total_duration)
            if v_clip:
                voice_layer = v_clip.with_volume_scaled(1.0) # Anchor volume: -6dB peak
                audio_layers.append(voice_layer)
                safe_print(f"🎤 [Track 1 - Voiceover Anchor] Uploaded Voice Applied ({v_clip.duration:.1f}s | Target: -6dB)")
        except Exception as ve:
            safe_print(f"⚠️ Track 1 Uploaded Voice load notice: {ve}")

    if voice_layer is None:
        if master_voiceover_path and os.path.exists(master_voiceover_path):
            try:
                v_clip = load_safe_audio_clip(master_voiceover_path)
                if v_clip and v_clip.duration > total_duration:
                    v_clip = v_clip.subclipped(0, total_duration)
                if v_clip:
                    voice_layer = v_clip.with_volume_scaled(1.0)
                    audio_layers.append(voice_layer)
                    safe_print(f"🎤 [Track 1 - Voiceover Anchor] Master TTS Voiceover Applied ({v_clip.duration:.1f}s | Target: -6dB)")
            except Exception as mve:
                safe_print(f"⚠️ Track 1 Master Voice notice: {mve}")

    if voice_layer is None and voice_clips:
        # Fallback: stitch per-scene audio clips
        try:
            curr = 0.0
            stitched = []
            for v_c in voice_clips:
                c_clip = load_safe_audio_clip(v_c)
                stitched.append(c_clip.with_start(curr))
                curr += getattr(c_clip, "duration", 3.5)
            voice_layer = CompositeAudioClip(stitched).with_volume_scaled(1.0)
            audio_layers.append(voice_layer)
            safe_print("🎤 [Track 1 - Voiceover Anchor] Per-Scene Voice Clips Stitched.")
        except Exception as st_err:
            safe_print(f"⚠️ Track 1 Stitched Voice notice: {st_err}")

    # Helper to safely extract duration from voice_clips items
    def _clip_duration(item):
        if hasattr(item, "duration") and item.duration:
            return float(item.duration)
        if isinstance(item, (tuple, list)) and len(item) > 1 and isinstance(item[1], (int, float)):
            return float(item[1])
        if isinstance(item, dict) and "duration" in item:
            return float(item["duration"])
        return 3.5

    # ─────────────────────────────────────────────────────────────────────────
    # TRACK 2: Real Foley & Micro SFX [-10 dB to -18 dB]
    # ─────────────────────────────────────────────────────────────────────────
    foley_clips = []
    curr_time = 0.0
    for i, sc in enumerate(scenes):
        sc_dur = _clip_duration(voice_clips[i]) if i < len(voice_clips) else 3.5
        # If scene has a fact card or statistic reveal, add foley pop/click
        if isinstance(sc, dict) and (sc.get("fact_card") or sc.get("emphasis_words")):
            if os.path.exists(sfx_library["pop"]):
                try:
                    foley_clip = load_safe_audio_clip(sfx_library["pop"]).with_volume_scaled(0.28) # Target: -14 dB
                    foley_clips.append(foley_clip.with_start(curr_time + 0.35))
                except Exception:
                    pass
        curr_time += sc_dur

    if foley_clips:
        audio_layers.append(CompositeAudioClip(foley_clips))
        safe_print(f"🔘 [Track 2 - Real Foley SFX] Added {len(foley_clips)} micro-foley sound elements (Target: -14dB).")

    # ─────────────────────────────────────────────────────────────────────────
    # TRACK 3: Cinematic / Emotional SFX (Whooshes, Hits, Risers) [-12 dB to -20 dB]
    # ─────────────────────────────────────────────────────────────────────────
    cinematic_sfx_clips = []
    curr_time = 0.0
    for i, v_c in enumerate(voice_clips):
        sc_dur = _clip_duration(v_c)
        # Transition Whoosh between scenes
        if i > 0 and os.path.exists(sfx_library["whoosh"]):
            try:
                whoosh_clip = load_safe_audio_clip(sfx_library["whoosh"]).with_volume_scaled(0.25) # Target: -16 dB
                cinematic_sfx_clips.append(whoosh_clip.with_start(max(0, curr_time - 0.15)))
            except Exception:
                pass

        # Heavy Bass Impact Hit on major visual reveal / first scene / location card
        if isinstance(scenes[i], dict) if i < len(scenes) else False:
            sc_info = scenes[i]
            if i == 0 or sc_info.get("map_location") or sc_info.get("fact_card"):
                if os.path.exists(sfx_library["impact"]):
                    try:
                        impact_clip = load_safe_audio_clip(sfx_library["impact"]).with_volume_scaled(0.22) # Target: -18 dB
                        cinematic_sfx_clips.append(impact_clip.with_start(curr_time + 0.10))
                    except Exception:
                        pass

        # Riser before mid-point or climax transition
        if i > 1 and i == len(voice_clips) // 2 and os.path.exists(sfx_library["riser"]):
            try:
                riser_clip = load_safe_audio_clip(sfx_library["riser"]).with_volume_scaled(0.20) # Target: -18 dB
                cinematic_sfx_clips.append(riser_clip.with_start(max(0, curr_time - 1.60)))
            except Exception:
                pass

        curr_time += sc_dur

    if cinematic_sfx_clips:
        audio_layers.append(CompositeAudioClip(cinematic_sfx_clips))
        safe_print(f"🎬 [Track 3 - Cinematic SFX] Applied {len(cinematic_sfx_clips)} transitions, heavy impact thuds & risers (Target: -16dB).")

    # ─────────────────────────────────────────────────────────────────────────
    # TRACK 4: Environmental & Ambience Layer (Atmosphere) [-20 dB to -28 dB]
    # ─────────────────────────────────────────────────────────────────────────
    ambience_path = generate_procedural_ambience(all_queries_text, total_duration)
    if ambience_path and os.path.exists(ambience_path):
        try:
            amb_clip = load_safe_audio_clip(ambience_path)
            if amb_clip and amb_clip.duration < total_duration:
                n_loops = int(math.ceil(total_duration / amb_clip.duration))
                amb_clip = CompositeAudioClip([amb_clip.with_start(j * amb_clip.duration) for j in range(n_loops)])
            if amb_clip:
                amb_clip = amb_clip.subclipped(0, total_duration).with_volume_scaled(0.10) # Target: -24 dB
                audio_layers.insert(0, amb_clip)
                safe_print("🌌 [Track 4 - Ambience Atmosphere Layer] Environmental Bed Multiplexed (Target: -24dB).")
        except Exception as amb_err:
            safe_print(f"⚠️ Track 4 Ambience notice: {amb_err}")

    # ─────────────────────────────────────────────────────────────────────────
    # TRACK 5: Background Music (MX - Underscore Track) [-20 dB to -30 dB + Auto-Ducking]
    # ─────────────────────────────────────────────────────────────────────────
    if config.get("enable_bg_music", True):
        music_path = fetch_background_music(config.get("ai_tone", "Cinematic & Epic"), visual_context=all_queries_text)
        if music_path and os.path.exists(music_path):
            try:
                bg_music = load_safe_audio_clip(music_path)
                if bg_music and bg_music.duration < total_duration:
                    n_loops = int(math.ceil(total_duration / bg_music.duration))
                    bg_music = CompositeAudioClip([bg_music.with_start(j * bg_music.duration) for j in range(n_loops)])
                # Lowers background music 3-6dB when creator speaks (-26dB), boosts during silence (-18dB)
                def dynamic_duck_volume(t):
                    is_speaking = False
                    curr = 0.0
                    for v_clip in voice_clips:
                        if curr <= t <= curr + v_clip.duration:
                            is_speaking = True
                            break
                        curr += v_clip.duration

                    # 10% volume (-26 dB) during voiceover, 30% volume (-18 dB) during pauses
                    return 0.10 if is_speaking else 0.30

                ducked_music = bg_music.with_volume_scaled(0.15)
                audio_layers.insert(0, ducked_music)
                safe_print("🎵 [Track 5 - Background Music] Underscore Track Applied (Target: -24dB).")
            except Exception as m_err:
                safe_print(f"⚠️ Track 5 Music notice: {m_err}")
                try:
                    bg_music = AudioFileClip(music_path).subclipped(0, total_duration).with_volume_scaled(0.12)
                    audio_layers.insert(0, bg_music)
                except Exception:
                    pass

    # ─────────────────────────────────────────────────────────────────────────
    # MASTER COMPOSITE: Layer all 5 Audio Tracks
    # ─────────────────────────────────────────────────────────────────────────
    master_audio = CompositeAudioClip(audio_layers).with_duration(total_duration)
    safe_print("✨ [5-Layer Master Audio Mix] Hollywood 5-Track Sound Design Mix Completed!")
    return master_audio
