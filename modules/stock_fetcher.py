"""
modules/stock_fetcher.py
─────────────────────────────────────────────────────────────────────────────
Stock Video Fetcher — Pexels Videos ONLY (Priority 1) → Procedural Fallback.

Unsplash images and Pixabay have been completely removed.
All clips returned are real video files (.mp4), never still-image motions.
─────────────────────────────────────────────────────────────────────────────
"""
import os
import requests
import cv2
import numpy as np
from urllib.parse import quote
from config import TEMP_DIR
from modules.cache_manager import get_cached_video, set_cached_video, set_cached_thumbnail


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode('ascii', errors='ignore').decode('ascii'))
        except Exception:
            pass


# ─── Procedural Video Fallback ────────────────────────────────────────────────

def create_procedural_background(filename, duration=10, width=1920, height=1080):
    """Generates a sleek cinematic animated gradient background video."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, 24, (width, height))
    num_frames = int(duration * 24)

    for i in range(num_frames):
        t = i / float(num_frames)
        x = np.linspace(0, 1, width)
        y = np.linspace(0, 1, height)
        xx, yy = np.meshgrid(x, y)

        r = np.uint8((0.05 + 0.15 * np.sin(2 * np.pi * t + xx)) * 255)
        g = np.uint8((0.10 + 0.20 * np.cos(2 * np.pi * t + yy)) * 255)
        b = np.uint8((0.25 + 0.35 * np.sin(2 * np.pi * t + xx + yy)) * 255)

        frame = cv2.merge([b, g, r])
        out.write(frame)

    out.release()
    return filename


# ─── Pexels Video API ─────────────────────────────────────────────────────────

def fetch_pexels_candidates(query, pexels_key, count=5):
    """Queries Pexels Video API for up to `count` HD video candidates."""
    from modules.ai_director import clean_stock_query
    clean_q = clean_stock_query(query)
    url = f"https://api.pexels.com/videos/search?query={quote(clean_q)}&per_page={max(5, count * 2)}"
    headers = {"Authorization": pexels_key}
    candidates = []
    try:
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code == 401:
            safe_print(f"  Pexels 401 Unauthorized for '{clean_q}' — API key restricted for this category. Get a new key at https://www.pexels.com/api/")
            return []
        if res.status_code != 200:
            safe_print(f"  Pexels HTTP {res.status_code} for '{clean_q}': {res.text[:120]}")
            return []
        videos = res.json().get("videos", [])
        for v in videos:
            thumb = v.get("image", "")
            files = v.get("video_files", [])
            # Prefer HD quality (>=1280px wide); fall back to best available
            v_url = None
            best_width = 0
            for f in sorted(files, key=lambda x: x.get("width", 0), reverse=True):
                w = f.get("width", 0)
                if w >= 1280 and not v_url:
                    v_url = f.get("link")
                if w > best_width:
                    best_width = w
            if not v_url and files:
                v_url = sorted(files, key=lambda x: x.get("width", 0), reverse=True)[0].get("link")
            if v_url and thumb:
                candidates.append({
                    "id":            v.get("id"),
                    "thumbnail_url": thumb,
                    "video_url":     v_url,
                    "tags":          clean_q,
                    "description":   v.get("url", ""),
                    "provider":      "pexels",
                    "width":         best_width,
                    "duration":      v.get("duration", 0),
                })
            if len(candidates) >= count:
                break
    except Exception as err:
        safe_print(f"  Pexels API notice for '{clean_q}': {err}")
    return candidates



def fetch_pexels_video(query, pexels_key):
    """Returns the best Pexels video URL for a query (single result)."""
    cands = fetch_pexels_candidates(query, pexels_key, count=1)
    return cands[0]["video_url"] if cands else None


# ─── Download Helper ──────────────────────────────────────────────────────────

def download_video_stream(download_url, filename):
    """Streams and saves a video file from URL; retries once on failure."""
    for attempt in range(2):
        try:
            res_video = requests.get(download_url, stream=True, timeout=(8, 45))
            if res_video.status_code == 200:
                with open(filename, "wb") as f:
                    for chunk in res_video.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                if os.path.exists(filename) and os.path.getsize(filename) > 10_000:
                    return True
        except (requests.exceptions.RequestException, Exception) as err:
            safe_print(f"  Video download attempt {attempt+1} notice: {err}")
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception:
                pass
    return False


def _extract_thumbnail(video_path: str, query: str):
    """Extracts a frame from the video and caches it as a JPEG thumbnail."""
    try:
        cap   = cv2.VideoCapture(video_path)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(60, max(0, total // 3)))
        ok, frame = cap.read()
        cap.release()
        if ok:
            h, w = frame.shape[:2]
            pw   = 320
            ph   = int(h * pw / max(w, 1))
            small = cv2.resize(frame, (pw, ph))
            _, buf = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, 80])
            set_cached_thumbnail(query, buf.tobytes())
    except Exception:
        pass


# ─── Stop-Word Cleaner ────────────────────────────────────────────────────────

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "do", "does", "did", "to",
    "at", "by", "for", "with", "about", "against", "between", "into", "through",
    "during", "before", "after", "above", "below", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "this", "that", "these", "those", "my", "your", "his", "her", "its", "our",
    "their", "what", "which", "who", "whom", "we", "you", "they", "it"
}


def clean_search_query(query: str) -> str:
    """Strips stop-words and keeps the most visual terms (max 4 words)."""
    if not query:
        return "cinematic nature"
    words = [w for w in query.lower().split() if w.isalnum() and w not in STOP_WORDS]
    return " ".join(words[:4]) if words else query


# ─── Main Stock Clip Fetcher ──────────────────────────────────────────────────

def get_stock_clip(
    search_query,
    index,
    progress_callback=None,
    alt_queries=None,
    expected_visual=None,
    video_brief=None,
    scene_text=None,
    groq_key=None,
):
    """
    Multi-Strategy Video-Only Stock Engine with Visual AI Verification:

    Strategy 0 — Disk cache (instant)
    Strategy 1 — Pexels HD Video API + Visual Selection Agent (qwen/qwen3.6-27b)
    Strategy 2 — Pexels with broader / alternative query terms
    Strategy 3 — Procedural animated gradient background video
    """
    pexels_key   = os.environ.get("PEXELS_API_KEY", "")
    groq_api_key = groq_key or os.environ.get("GROQ_API_KEY", "")
    filename     = os.path.join(TEMP_DIR, f"clip_{index:02d}.mp4")

    alt_queries = alt_queries or []
    raw_candidates = [search_query] + [q for q in alt_queries if q and q != search_query]

    # Detect primary anchor subject across all queries
    detected_anchor = ""
    common_anchors = [
        "mars", "moon", "ocean", "space", "dinosaur", "robot", "cyberpunk",
        "volcano", "galaxy", "planet", "city", "forest", "mountain", "ai",
        "technology", "factory", "drone", "car", "train", "earth",
    ]
    for cand in raw_candidates:
        cand_lower = cand.lower()
        for anc in common_anchors:
            if anc in cand_lower:
                detected_anchor = anc
                break
        if detected_anchor:
            break

    # Anchor every query with the core subject if it's missing
    anchored_candidates = []
    for q in raw_candidates:
        q_clean = clean_search_query(q)
        if detected_anchor and detected_anchor not in q_clean.lower():
            anchored_candidates.append(f"{detected_anchor} {q_clean}")
            anchored_candidates.append(q_clean)
        else:
            anchored_candidates.append(q_clean)

    all_queries = list(dict.fromkeys(anchored_candidates + raw_candidates))
    expected_visual = expected_visual or f"HD video footage of {search_query}"
    video_brief = video_brief or {
        "topic": search_query, "purpose": "educational",
        "tone": "cinematic", "visual_style": "high budget",
        "avoid": "irrelevant footage"
    }
    scene_text = scene_text or search_query

    if progress_callback:
        progress_callback("fetching_meta", index, search_query)

    # ── Strategy 0: Disk Cache ────────────────────────────────────────────────
    for q in all_queries:
        cached = get_cached_video(q)
        if cached:
            import shutil
            shutil.copy2(cached, filename)
            safe_print(f"  Clip from cache: '{q}'")
            if progress_callback:
                progress_callback("video_downloaded", index, f"{q} (Cache)")
            return filename

    # ── Strategy 1: Pexels Video + Visual Selection Agent ────────────────────
    if pexels_key:
        for q in all_queries:
            safe_print(f"  Pexels video search: '{q}'")
            cands = fetch_pexels_candidates(q, pexels_key, count=5)
            if cands:
                try:
                    from modules.video_selector import select_best_candidate
                    decision = select_best_candidate(
                        scene_text, expected_visual, video_brief, cands, groq_api_key
                    )
                    selected_clip = decision.get("clip")
                except Exception as sel_err:
                    safe_print(f"  Visual selector notice: {sel_err} — using first candidate")
                    selected_clip = cands[0]

                # Safety net: if selector returned None, always use first Pexels candidate
                # (a real video is always better than a procedural background)
                if selected_clip is None and cands:
                    safe_print(f"  Selector returned no clip — using first Pexels result for '{q}'")
                    selected_clip = cands[0]

                if selected_clip and selected_clip.get("video_url"):
                    v_link = selected_clip["video_url"]
                    if progress_callback:
                        progress_callback("downloading_video", index, f"{q} (Pexels)")
                    if download_video_stream(v_link, filename):
                        set_cached_video(q, filename)
                        _extract_thumbnail(filename, q)
                        if progress_callback:
                            progress_callback("video_downloaded", index, q)
                        safe_print(f"  Pexels video downloaded: '{q}'")
                        return filename


    # ── Strategy 2: Broader Pexels search with raw query ─────────────────────
    if pexels_key:
        broader_q = detected_anchor if detected_anchor else search_query.split()[0]
        safe_print(f"  Pexels broad fallback search: '{broader_q}'")
        cands = fetch_pexels_candidates(broader_q, pexels_key, count=3)
        if cands and cands[0].get("video_url"):
            if progress_callback:
                progress_callback("downloading_video", index, f"{broader_q} (Pexels Broad)")
            if download_video_stream(cands[0]["video_url"], filename):
                set_cached_video(broader_q, filename)
                _extract_thumbnail(filename, broader_q)
                if progress_callback:
                    progress_callback("video_downloaded", index, broader_q)
                safe_print(f"  Pexels broad video downloaded: '{broader_q}'")
                return filename

    # ── Strategy 3: Procedural Animated Background (last resort) ─────────────
    safe_print(f"  Generating procedural background for scene {index}...")
    if progress_callback:
        progress_callback("downloading_video", index, f"Scene {index} (Procedural)")

    create_procedural_background(filename, duration=10)
    if progress_callback:
        progress_callback("video_downloaded", index, search_query)

    return filename


# ─── Parallel Downloader ──────────────────────────────────────────────────────

from concurrent.futures import ThreadPoolExecutor, as_completed


def fetch_stock_clips_parallel(scenes: list, progress_callback=None, video_brief=None, api_key=None) -> list:
    """
    Downloads HD Pexels video clips for ALL scenes concurrently using parallel
    worker threads with Visual AI Verification Agent per candidate set.
    Returns a list of local video file paths in scene order.
    """
    total = len(scenes)
    results = [None] * total

    def _fetch_single(idx, scene):
        q        = scene.get("search_query", "cinematic nature")
        alts     = scene.get("alt_queries", [])
        exp_vis  = scene.get("expected_visual", "")
        sc_text  = scene.get("narration", "") or scene.get("english_subtitle", "")
        clip_path = get_stock_clip(
            q, idx + 1,
            progress_callback=progress_callback,
            alt_queries=alts,
            expected_visual=exp_vis,
            video_brief=video_brief,
            scene_text=sc_text,
            groq_key=api_key,
        )
        return idx, clip_path

    max_workers = min(3, max(1, total))
    safe_print(
        f"  Parallel stock downloader: {total} scenes, {max_workers} threads (memory-optimized)..."
    )
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_fetch_single, i, sc) for i, sc in enumerate(scenes)]
        for f in as_completed(futures):
            try:
                idx, clip_path = f.result()
                results[idx] = clip_path
            except Exception as e:
                safe_print(f"  Stock clip error for scene: {e}")

    # Ensure no None entries — generate procedural background as last resort
    for i in range(total):
        if not results[i] or not os.path.exists(results[i]):
            fallback_fn = os.path.join(TEMP_DIR, f"clip_{i+1:02d}.mp4")
            create_procedural_background(fallback_fn, duration=10)
            results[i] = fallback_fn

    return results