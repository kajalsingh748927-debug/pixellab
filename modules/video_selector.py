"""
modules/video_selector.py
─────────────────────────────────────────────────────────────────────────────
Smart Video Selection Engine for Pixelab.

Two-stage selection pipeline:
  Stage 1 — Text Matching (fast, free, no API call)
    • Extracts human-readable title from the Pexels page URL slug
      e.g. /video/a-walking-robot-8566674/ → "a walking robot"
    • Extracts keyword tags from the thumbnail filename
      e.g. abstract-ai-android-art-8566674.jpeg → "abstract ai android art"
    • Scores every candidate by keyword overlap with scene narration +
      expected_visual + search_query.
    • Re-ranks candidates so the most text-relevant ones go first.

  Stage 2 — Groq Vision AI (qwen/qwen3.6-27b)
    • Takes top MAX_CANDIDATES after text-ranking.
    • Sends thumbnail images + enriched description block (title + tags +
      overlap score) to the Vision LLM.
    • LLM returns best_index + confidence + reason.
    • If confidence ≥ MIN_CONFIDENCE → use that candidate.
    • Otherwise → use highest-text-score candidate as fallback.
─────────────────────────────────────────────────────────────────────────────
"""
import re
import json
from groq import Groq

SELECTION_MODEL = "qwen/qwen3.6-27b"
MIN_CONFIDENCE  = 0.45   # Vision model threshold; below this we still use top text-scored candidate
MAX_CANDIDATES  = 2      # Max thumbnails sent to Vision AI (keeps token usage low)


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="ignore").decode("ascii"))
        except Exception:
            pass


# ─── Stage 1: Text Extraction & Scoring ──────────────────────────────────────

def _extract_title_from_url(pexels_url: str) -> str:
    """
    Extracts a human-readable title from a Pexels page URL slug.
    e.g. 'https://www.pexels.com/video/a-walking-robot-8566674/'
         → 'a walking robot'
    """
    if not pexels_url:
        return ""
    # Match the slug part between /video/ and the trailing ID/slash
    m = re.search(r"/video/([a-z0-9\-]+?)(?:-\d+)?/?$", pexels_url.lower())
    if m:
        return m.group(1).replace("-", " ").strip()
    return ""


def _extract_tags_from_thumbnail(thumbnail_url: str) -> str:
    """
    Extracts keyword tags embedded in the Pexels thumbnail filename.
    e.g. 'abstract-ai-android-art-8566674.jpeg'
         → 'abstract ai android art'
    """
    if not thumbnail_url:
        return ""
    # Get just the filename without path and extension
    fname = thumbnail_url.split("/")[-1].split("?")[0]           # e.g. abstract-ai-android-art-8566674.jpeg
    fname = re.sub(r"\.\w+$", "", fname)                          # strip extension
    fname = re.sub(r"-?\d{5,}$", "", fname)                       # strip trailing ID number
    return fname.replace("-", " ").strip()


def _text_overlap_score(text_a: str, text_b: str) -> float:
    """
    Returns the Jaccard-like word overlap score between two strings.
    Score = |intersection| / |union|  (0.0 to 1.0)
    Ignores common stop-words.
    """
    _STOP = {"a", "an", "the", "of", "in", "on", "at", "to", "and", "or",
             "with", "for", "is", "are", "was", "this", "that", "by"}
    def _tokens(s):
        return {w for w in re.sub(r"[^\w\s]", " ", s.lower()).split() if w not in _STOP and len(w) > 1}
    a = _tokens(text_a)
    b = _tokens(text_b)
    if not a or not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union)


def score_and_rank_candidates(
    candidates: list[dict],
    scene_text: str,
    expected_visual: str,
    search_query: str,
) -> list[dict]:
    """
    Stage 1: Enrich every candidate with extracted description + text score,
    then re-rank from highest to lowest score.

    Adds to each candidate dict:
        'title'       — human-readable title from Pexels URL slug
        'thumb_tags'  — keyword tags from thumbnail filename
        'description_text' — combined description for AI prompt
        'text_score'  — float 0.0–1.0 keyword overlap score
    """
    reference = f"{scene_text} {expected_visual} {search_query}".lower()

    for c in candidates:
        title      = _extract_title_from_url(c.get("description", "") or c.get("url", ""))
        thumb_tags = _extract_tags_from_thumbnail(c.get("thumbnail_url", ""))
        desc_text  = f"{title} {thumb_tags}".strip()

        # Keyword overlap against scene reference
        score = _text_overlap_score(desc_text, reference)

        c["title"]            = title
        c["thumb_tags"]       = thumb_tags
        c["description_text"] = desc_text or c.get("tags", "")
        c["text_score"]       = round(score, 3)

    # Sort: highest text_score first
    ranked = sorted(candidates, key=lambda x: x.get("text_score", 0.0), reverse=True)
    return ranked


# ─── Stage 2: Groq Vision AI Selection ───────────────────────────────────────

def select_best_candidate(
    scene_text: str,
    expected_visual: str,
    video_brief: dict,
    candidates: list[dict],
    api_key: str,
) -> dict:
    """
    Two-stage smart video selection:
      Stage 1 — Text matching + keyword overlap re-ranking (free, instant)
      Stage 2 — Groq Vision AI inspects top-N thumbnails + enriched descriptions

    Returns
    -------
    dict
        {selected_id, confidence, reason, clip, text_score}
    """
    if not candidates:
        return {"selected_id": None, "confidence": 0.0, "reason": "No candidates", "clip": None}

    # ── Stage 1: Text Scoring ─────────────────────────────────────────────────
    search_query = candidates[0].get("tags", scene_text)  # tags field = original query
    ranked = score_and_rank_candidates(candidates, scene_text, expected_visual, search_query)

    safe_print(f"  Text scores: " +
               " | ".join(f"#{i+1} {c['title'][:20]!r} {c['text_score']:.2f}"
                          for i, c in enumerate(ranked[:MAX_CANDIDATES])))

    # If no Groq key — return highest text-scored candidate
    if not api_key:
        best = ranked[0]
        safe_print(f"  No Groq key — using top text-scored candidate: '{best['title']}'")
        return {"selected_id": best.get("id"), "confidence": best["text_score"],
                "reason": f"Top text score ({best['text_score']:.2f}): {best['description_text']}", "clip": best}

    # ── Stage 2: Vision AI ────────────────────────────────────────────────────
    client = Groq(api_key=api_key)
    shortlist = [c for c in ranked if c.get("thumbnail_url")][:MAX_CANDIDATES]

    if not shortlist:
        best = ranked[0]
        return {"selected_id": best.get("id"), "confidence": best["text_score"],
                "reason": "No thumbnails — text score fallback", "clip": best}

    # Build enriched candidate description block for the AI prompt
    candidates_info_lines = []
    for i, c in enumerate(shortlist, start=1):
        title      = c.get("title", "unknown")
        thumb_tags = c.get("thumb_tags", "")
        dur        = c.get("duration", "?")
        res        = f"{c.get('width', '?')}px wide"
        t_score    = c.get("text_score", 0.0)
        candidates_info_lines.append(
            f"Candidate #{i}:\n"
            f"  Title (from Pexels URL): '{title}'\n"
            f"  Thumbnail tags: '{thumb_tags}'\n"
            f"  Duration: {dur}s | Resolution: {res}\n"
            f"  Text-match score vs scene: {t_score:.2f}/1.00"
        )
    cand_block = "\n\n".join(candidates_info_lines)

    prompt_text = (
        f"You are an expert film editor selecting the best stock video clip for one scene.\n\n"
        f"VIDEO TOPIC: {video_brief.get('topic', 'General')}\n"
        f"VIDEO TONE: {video_brief.get('tone', 'Cinematic')}\n"
        f"VISUAL STYLE: {video_brief.get('visual_style', 'Clean High Quality')}\n"
        f"THINGS TO AVOID: {video_brief.get('avoid', 'Irrelevant visuals')}\n\n"
        f"SCENE NARRATION: \"{scene_text}\"\n"
        f"IDEAL SHOT: {expected_visual}\n\n"
        f"CANDIDATES (thumbnails follow in numbered order):\n{cand_block}\n\n"
        "Pick the ONE candidate whose thumbnail, title, and tags best match the ideal shot "
        "and avoid the AVOID list. A higher text-match score means better keyword alignment "
        "but visuals are the primary factor.\n\n"
        "Return ONLY a JSON object with exactly these three keys: "
        "best_index (integer 1 or 2, or null if none match), "
        "confidence (number between 0 and 1), "
        "reason (one sentence string)."
    )


    content = [{"type": "text", "text": prompt_text}]
    for c in shortlist:
        content.append({"type": "image_url", "image_url": {"url": c["thumbnail_url"]}})

    try:
        response = client.chat.completions.create(
            model=SELECTION_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert film editor. You MUST output valid JSON format with keys best_index, confidence, and reason."},
                {"role": "user", "content": content}
            ],
            response_format={"type": "json_object"},
            timeout=18,
        )
        parsed     = json.loads(response.choices[0].message.content)
        idx        = parsed.get("best_index")
        confidence = float(parsed.get("confidence", 0.0))
        reason     = parsed.get("reason", "No reason")

        if idx and isinstance(idx, int) and 1 <= idx <= len(shortlist) and confidence >= MIN_CONFIDENCE:
            selected = shortlist[idx - 1]
            safe_print(
                f"  Vision AI APPROVED #{idx} '{selected.get('title', '')}' "
                f"[Conf: {confidence:.2f} | TxtScore: {selected['text_score']:.2f}] — {reason}"
            )
            return {"selected_id": selected.get("id"), "confidence": confidence,
                    "reason": reason, "clip": selected, "text_score": selected["text_score"]}
        else:
            # Low confidence — fall back to highest text-score candidate
            fallback = shortlist[idx - 1] if (idx and 1 <= idx <= len(shortlist)) else ranked[0]
            safe_print(
                f"  Vision AI low-conf ({confidence:.2f}) — using text-top: '{fallback.get('title', '')}' "
                f"[TxtScore: {fallback['text_score']:.2f}]"
            )
            return {"selected_id": fallback.get("id"), "confidence": confidence,
                    "reason": f"Text-score fallback: {reason}", "clip": fallback,
                    "text_score": fallback["text_score"]}

    except Exception as e:
        safe_print(f"  Vision AI error: {e} — using top text-scored candidate")
        best = ranked[0]
        return {"selected_id": best.get("id"), "confidence": best["text_score"],
                "reason": f"Vision error fallback: {e}", "clip": best,
                "text_score": best["text_score"]}
