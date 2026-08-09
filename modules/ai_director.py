"""
modules/ai_director.py
─────────────────────────────────────────────────────────────────────────────
AI Director & Storyboard Generator for Pixelab.

Ingests full video scripts or transcribed scenes and uses Groq LLMs
(default: openai/gpt-oss-120b) to generate:
  1. Video Brief: One-time lock of topic, purpose, tone, visual style, & avoid rules.
  2. Scene Breakdown & Search Queries: Anchored stock video search terms.
  3. Expected Visuals: Literal shot description for visual verification agent.
  4. 100% English Subtitles: Translated kinetic subtitles regardless of voiceover language.
  5. Emphasis Words, Map Locations, Fact Cards.
─────────────────────────────────────────────────────────────────────────────
"""
import json
import re
from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "llama-3.3-70b-versatile"


def safe_print(msg):
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="ignore").decode("ascii"))
        except Exception:
            pass


TONE_PROMPTS = {
    "Cinematic & Epic":   "Use powerful, dramatic language. Build tension and awe.",
    "Documentary":        "Use factual, informative, and measured tone.",
    "Motivational":       "Use inspiring, energetic, action-driven language.",
    "News Style":         "Use clear, objective, journalistic tone.",
    "Story Narrative":    "Use storytelling with characters and emotion.",
    "Educational":        "Use simple, clear, explanatory language.",
    "Dramatic":           "Use emotional, high-stakes, suspenseful language.",
}

LANG_PROMPTS = {
    "English":   "Write in English.",
    "Hindi":     "Write in Hindi (Devanagari script).",
    "Hinglish":  "Write in Hinglish (mix of Hindi and English).",
    "Spanish":   "Write in Spanish.",
    "French":    "Write in French.",
    "German":    "Write in German.",
    "Arabic":    "Write in Arabic.",
}


def _call_groq_json(client: Groq, prompt: str, system_prompt: str = "") -> dict:
    """Helper to query Groq with primary model and automatic fallback."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        chat = client.chat.completions.create(
            messages=messages,
            model=DEFAULT_MODEL,
            response_format={"type": "json_object"}
        )
        return json.loads(chat.choices[0].message.content)
    except Exception as e1:
        safe_print(f"⚠️ Groq primary model '{DEFAULT_MODEL}' notice: {e1} — trying fallback '{FALLBACK_MODEL}'...")
        try:
            chat = client.chat.completions.create(
                messages=messages,
                model=FALLBACK_MODEL,
                response_format={"type": "json_object"}
            )
            return json.loads(chat.choices[0].message.content)
        except Exception as e2:
            safe_print(f"❌ Groq fallback model failed: {e2}")
            raise e2


def generate_video_brief(script_text: str, api_key: str) -> dict:
    """
    One-time call before scene splitting. Locks the video's overall topic, purpose,
    tone, visual style, and things to avoid so scene-level decisions stay anchored.
    """
    if not api_key:
        return {
            "topic": "General Topic",
            "purpose": "educational",
            "tone": "cinematic and informative",
            "visual_style": "High budget broadcast footage, clear visuals, cinematic lighting",
            "avoid": "People smoking, irrelevant bubbles, random urban street footage"
        }

    client = Groq(api_key=api_key)
    prompt = f"""
You are a documentary visual director reviewing a full script before production begins.

SCRIPT / TOPIC:
{script_text}

Return ONLY a JSON object with these exact keys:
- "topic": the single main subject (e.g. "Mars", "Personal Finance", "Ancient Rome", "Ocean Deep")
- "purpose": one of ["educational", "promotional", "storytelling", "news", "motivational", "entertainment"]
- "tone": one or two words (e.g. "serious and awe-inspiring", "fun and energetic")
- "visual_style": one sentence describing ideal footage
  (e.g. "real space/NASA footage, cosmic landscapes, high quality 4k, no irrelevant people")
- "avoid": short string listing things that would look WRONG even if keyword-matched
  (e.g. for "Mars atmosphere carbon dioxide", avoid people smoking cigarettes or soap bubbles)
"""
    try:
        brief = _call_groq_json(client, prompt)
        safe_print(f"📋 Video Brief Generated — Topic: '{brief.get('topic')}' | Purpose: '{brief.get('purpose')}'")
        return brief
    except Exception as e:
        safe_print(f"⚠️ Video Brief fallback due to error: {e}")
        return {
            "topic": script_text.split("\n")[0][:30],
            "purpose": "educational",
            "tone": "cinematic",
            "visual_style": "High-quality broadcast visual footage",
            "avoid": "Irrelevant clips, low quality footage, cigarette smoking"
        }


def analyze_script(script_text, api_key, scene_count=4, word_length="8 to 12 words",
                   tone="Cinematic & Epic", language="English", video_brief=None):
    if not api_key:
        print("⚠️ Groq API key missing.")
        return []

    client = Groq(api_key=api_key)
    brief = video_brief or generate_video_brief(script_text, api_key)

    tone_instruction = TONE_PROMPTS.get(tone, "")
    lang_instruction = LANG_PROMPTS.get(language, "Write in English.")

    if str(scene_count).upper() == "AUTO" or not isinstance(scene_count, int):
        scene_count_str = "the OPTIMAL number of (e.g. 2 to 15 depending on script length)"
    else:
        scene_count_str = f"EXACTLY {scene_count}"

    system_instruction = (
        f"You are a master Hollywood visual director and stock video researcher. "
        f"VIDEO BRIEF CONTEXT: Topic='{brief.get('topic')}', Tone='{brief.get('tone')}', Style='{brief.get('visual_style')}', Avoid='{brief.get('avoid')}'. "
        f"CORE PURPOSE & SUBJECT ANCHOR RULE: EVERY single 'search_query' and 'alt_queries' MUST be strictly anchored to '{brief.get('topic')}'. "
        f"CONCISE QUERY RULE: Every 'search_query' and 'alt_queries' MUST be 3 to 5 core visual keywords ONLY (Noun + Verb). STRICTLY PROHIBITED words in queries: '4K', 'HD', 'footage', 'high resolution', 'cinematic', 'video of', 'clip of'. Example: write 'robotics lab ai screens' NOT '4K high resolution video of robotics lab'. "
        f"MAXIMUM DYNAMIC SCENES RULE: Break script into MAXIMUM possible fast-paced scenes ({scene_count_str}) changing every 2 to 4 seconds (6 to 10 words per scene). "
        f"CRITICAL: Regardless of script language, generate 'search_query', 'alt_queries', and 'expected_visual' in 100% PLAIN ENGLISH ONLY. "
        f"EXPECTED VISUAL RULE: Provide 'expected_visual' — a short, literal visual description of the ideal shot for this scene (e.g. 'wide shot of orange red dust storm sweeping across Martian surface, no people, no text'). "
        f"ALSO provide 'english_subtitle': punchy English translation for kinetic subtitles. "
        f"ALSO provide 'emphasis_words': key numbers or impact words for spring-zoom. "
        f"ALSO provide optional 'map_location' (UPPERCASE) and 'fact_card' object. "
        f"Tone: {tone_instruction} "
        f"Language: {lang_instruction} "
        "For each scene return: "
        "1. 'narration': Voiceover text in requested script language. "
        "2. 'english_subtitle': Clean English translation. "
        "3. 'expected_visual': Literal description of ideal shot matching topic. "
        "4. 'search_query': Primary ENGLISH ONLY search query (3-5 keywords max, NO 4K/HD/footage). "
        "5. 'alt_queries': List of 2 backup search queries (3-5 keywords max). "
        "6. 'emphasis_words': List of 1-3 impact words/numbers. "
        "7. 'map_location': Optional location string or null. "
        "8. 'fact_card': Optional object with 'label' and 'value' or null. "
        "Return ONLY a JSON object with a 'scenes' array."
    )

    try:
        parsed = _call_groq_json(client, f"Script:\n{script_text}", system_prompt=system_instruction)
        scenes = parsed.get("scenes", [])
        for sc in scenes:
            sc["search_query"] = clean_stock_query(sc.get("search_query", "nature"))
            raw_alts = sc.get("alt_queries", [])
            sc["alt_queries"] = [clean_stock_query(q) for q in raw_alts if q]
            if not sc.get("english_subtitle"):
                sc["english_subtitle"] = sc.get("narration", "")
            if not sc.get("expected_visual"):
                sc["expected_visual"] = f"Visual shot of {sc['search_query']}"
            sc["emphasis_words"] = [str(w).upper().strip() for w in sc.get("emphasis_words", []) if w]
            if sc.get("map_location"):
                sc["map_location"] = str(sc["map_location"]).upper().strip()
        return scenes
    except Exception as e:
        safe_print(f"AI Director error: {str(e).encode('ascii', errors='replace').decode('ascii')}")
        return []


def _ascii_query(text: str) -> str:
    """Strips non-ASCII characters and clean stock query keywords."""
    return clean_stock_query(text)


FILLER_WORDS = {
    "4k", "hd", "high", "resolution", "ultra", "res", "footage", "video",
    "clip", "shot", "cinematic", "stock", "showing", "of", "the", "a", "an",
    "and", "in", "on", "with", "into", "for", "by", "scene", "background"
}


def clean_stock_query(text: str, max_words: int = 5) -> str:
    """
    Strips noise/filler words (4K, HD, high resolution, footage of) and limits 
    query to 3-5 core visual keywords for maximum stock API search accuracy.
    """
    if not text:
        return "nature"
    
    raw = text.encode("ascii", errors="ignore").decode("ascii").lower().strip()
    
    phrases_to_remove = [
        "high resolution footage of", "high resolution footage", "high resolution video of",
        "high resolution video", "high resolution", "4k footage of", "4k footage",
        "4k video of", "4k video", "hd footage of", "hd footage", "hd video of",
        "cinematic footage of", "stock footage of", "video of", "footage of", "clip of"
    ]
    for ph in phrases_to_remove:
        raw = raw.replace(ph, "")

    tokens = [re.sub(r"[^\w]", "", w) for w in raw.split()]
    filtered = [w for w in tokens if w and w not in FILLER_WORDS]

    if not filtered:
        filtered = [w for w in tokens if w]

    clean_res = " ".join(filtered[:max_words]).strip()
    return clean_res if clean_res else "nature"


STOP_WORDS = {
    "for", "decades", "existed", "purely", "behind", "but", "a", "an", "the",
    "and", "or", "in", "on", "at", "to", "from", "by", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below",
    "up", "down", "off", "over", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "any", "both", "each", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "should",
    "now", "steps", "happening", "as", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "having", "do", "does", "did", "doing", "would",
    "could", "ought", "i", "you", "he", "she", "it", "we", "they", "them", "their",
    "this", "that", "these", "those"
}


def extract_visual_keywords(narration: str, topic: str = "") -> str:
    """
    Extracts high-value visual nouns/adjectives from narration and anchors them to the video topic.
    Never outputs sentence fragments like 'for decades artificial' or 'but a massive'.
    """
    if not narration:
        return clean_stock_query(topic) if topic else "nature"

    raw = narration.encode("ascii", errors="ignore").decode("ascii").lower()
    words = [re.sub(r"[^\w]", "", w) for w in raw.split()]
    
    nouns_and_keywords = [w for w in words if w and len(w) > 2 and w not in STOP_WORDS and w not in FILLER_WORDS]
    
    topic_clean = clean_stock_query(topic) if topic else ""
    topic_words = topic_clean.split() if topic_clean else []
    
    result_words = []
    for tw in topic_words:
        if tw not in result_words:
            result_words.append(tw)
            
    for kw in nouns_and_keywords:
        if kw not in result_words:
            result_words.append(kw)
        if len(result_words) >= 4:
            break

    final_q = " ".join(result_words[:4]).strip()
    return final_q if final_q else (topic_clean or "nature")


def analyze_transcript(scenes: list, api_key: str, tone: str = "Cinematic & Epic", video_brief=None) -> list:
    """
    Custom Audio Mode — AI Director with Deep Visual Script Analysis & English Subtitle Translation.
    """
    full_narration = " ".join(sc.get("narration", "") for sc in scenes)
    brief = video_brief or (generate_video_brief(full_narration, api_key) if api_key else {})
    topic = brief.get("topic", "")

    if not api_key:
        safe_print("Groq API key missing — search queries will be extracted from narration nouns.")
        for sc in scenes:
            sc["search_query"] = extract_visual_keywords(sc.get("narration", ""), topic=topic)
            sc["alt_queries"]  = [clean_stock_query(topic + " landscape"), clean_stock_query(topic + " background")]
            sc["expected_visual"] = f"Visual shot of {sc['search_query']}"
            sc["english_subtitle"] = sc.get("narration", "")
            words = sc.get("narration", "").split()
            sc["emphasis_words"]   = [w.upper() for w in words if any(c.isdigit() for c in w)]
        return scenes

    scene_count = len(scenes)
    tone_hint   = TONE_PROMPTS.get(tone, "")

    scene_lines = "\n".join(
        f"Scene {i+1}: \"{sc.get('narration', '').strip()}\""
        for i, sc in enumerate(scenes)
    )

    system_instruction = (
        f"You are a master Hollywood visual director and stock footage researcher. "
        f"VIDEO BRIEF CONTEXT: Topic='{brief.get('topic')}', Tone='{brief.get('tone')}', Style='{brief.get('visual_style')}', Avoid='{brief.get('avoid')}'. "
        f"CORE PURPOSE & SUBJECT ANCHOR RULE: EVERY 'search_query' and 'alt_queries' MUST be strictly anchored to '{brief.get('topic')}'. "
        f"CONCISE QUERY RULE: Every 'search_query' MUST be 3 to 5 core visual Noun + Verb keywords (e.g. 'ai text prompts code generation' or 'robot monitor screen emerging'). "
        f"STRICTLY PROHIBITED: NEVER output sentence fragments like 'for decades artificial', 'but a massive', 'steps out of', or 'physical world through'. NEVER use '4K', 'HD', 'footage', 'video of'. "
        f"EXPECTED VISUAL RULE: Generate 'expected_visual': a short, literal description of ideal shot for visual verification. "
        f"CRITICAL: Generate 'search_query', 'alt_queries', and 'expected_visual' in 100% PLAIN ENGLISH ONLY. "
        f"ALSO generate 'english_subtitle': clean 100% English translation of the narration for kinetic subtitles. "
        f"ALSO generate 'emphasis_words': key impact words for spring-zoom. "
        f"ALSO generate optional 'map_location' and 'fact_card'. "
        f"For each scene return: "
        f"1. 'english_subtitle': Clean English translation. "
        f"2. 'expected_visual': Literal description of ideal shot. "
        f"3. 'search_query': Primary ENGLISH ONLY visual search query anchored to '{brief.get('topic')}'. "
        f"4. 'alt_queries': List of 2 backup search terms. "
        f"5. 'emphasis_words': Key impact numbers/words. "
        f"6. 'map_location': Optional location or null. "
        f"7. 'fact_card': Optional fact object or null. "
        f"Return ONLY a JSON object with a 'scenes' array of {scene_count} objects."
    )

    client = Groq(api_key=api_key)
    try:
        parsed = _call_groq_json(client, f"Scenes:\n{scene_lines}", system_prompt=system_instruction)
        llm_scenes = parsed.get("scenes", [])

        for i, sc in enumerate(scenes):
            narration_txt = sc.get("narration", "")
            smart_fallback = extract_visual_keywords(narration_txt, topic=topic)

            if i < len(llm_scenes):
                raw_q = llm_scenes[i].get("search_query", "").strip()
                raw_alts = llm_scenes[i].get("alt_queries", [])
                raw_eng_sub = llm_scenes[i].get("english_subtitle", "").strip()
                raw_vis = llm_scenes[i].get("expected_visual", "").strip()
                raw_emph = llm_scenes[i].get("emphasis_words", [])

                clean_q = clean_stock_query(raw_q)
                # Check if query is a sentence fragment
                if not clean_q or any(clean_q.startswith(frag) for frag in ["for decades", "but a", "steps out", "physical world"]):
                    clean_q = smart_fallback

                sc["search_query"] = clean_q
                sc["alt_queries"]  = [clean_stock_query(q) for q in raw_alts if q] or [smart_fallback]
                sc["expected_visual"] = raw_vis or f"Visual shot of {sc['search_query']}"
                sc["english_subtitle"] = raw_eng_sub or narration_txt
                sc["emphasis_words"] = [str(w).upper().strip() for w in raw_emph if w]
            else:
                sc["search_query"] = smart_fallback
                sc["alt_queries"]  = [clean_stock_query(topic + " landscape")]
                sc["expected_visual"] = f"Visual shot of {sc['search_query']}"
                sc["english_subtitle"] = narration_txt
                words = narration_txt.split()
                sc["emphasis_words"]   = [w.upper() for w in words if any(c.isdigit() for c in w)]

        safe_print(f"AI Director: queries, expected visuals, and English subtitles generated for {len(scenes)} scenes.")
        return scenes

    except Exception as e:
        err_msg = str(e).encode("ascii", errors="replace").decode("ascii")
        safe_print(f"AI Director (analyze_transcript) notice: {err_msg}")
        for sc in scenes:
            narration_txt = sc.get("narration", "")
            sc["search_query"] = extract_visual_keywords(narration_txt, topic=topic)
            sc["alt_queries"]  = [clean_stock_query(topic + " background")]
            sc["expected_visual"] = f"Visual shot of {sc['search_query']}"
            sc["english_subtitle"] = narration_txt
        return scenes