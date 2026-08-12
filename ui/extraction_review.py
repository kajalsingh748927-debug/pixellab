"""
ui/extraction_review.py
─────────────────────────────────────────────────────────────────────────────
Extraction Review Screen Component for Pixelab.

Displays extracted Video Titles and Facts on a single review panel:
  1. Top Section — Main Title, Character Count, and Collapsible Backup Ideas
  2. Bottom Section — Numbered Facts with Confidence Color Badges
     • 🟢 Green = High Confidence
     • 🟡 Yellow = Medium Confidence
     • 🔴 Red = Low Confidence
     • Category tag + Greyed-out Source Snippet for truthfulness verification
  3. Action Buttons — "✅ Approve — Looks Good" & "↩️ Re-extract"
─────────────────────────────────────────────────────────────────────────────
"""
import time
import numpy as np
import streamlit as st
from modules.ai_director import extract_title_and_facts


def auto_align_facts_to_timeline(facts: list, word_timestamps: list = None) -> list:
    """
    Matches extracted fact text against Whisper audio word_timestamps to auto-assign
    exact timeline start seconds where spoken in the narration.
    """
    if not facts:
        return facts

    if not word_timestamps or not isinstance(word_timestamps, list):
        for i, f in enumerate(facts):
            if "start_sec" not in f:
                f["start_sec"] = round(float(i * 3.5), 2)
        return facts

    full_words = [str(w.get("word", "")).lower().strip(".,!?:;\"'") for w in word_timestamps if isinstance(w, dict)]

    for f_idx, fact in enumerate(facts):
        f_text = str(fact.get("text", "")).lower()
        f_words = [w.strip(".,!?:;\"'") for w in f_text.split() if len(w) > 2]

        match_start = None
        if len(f_words) >= 2:
            for i in range(len(full_words) - 1):
                if full_words[i] in f_words and full_words[i + 1] in f_words:
                    match_start = word_timestamps[i].get("start", 0.0)
                    break

        if match_start is None and f_words:
            for i, w in enumerate(full_words):
                if w in f_words:
                    match_start = word_timestamps[i].get("start", 0.0)
                    break

        if match_start is not None:
            fact["start_sec"] = round(float(match_start), 2)
        elif "start_sec" not in fact:
            fact["start_sec"] = round(float(f_idx * 3.5), 2)

    return facts


def render_extraction_review_panel(script_text: str, word_timestamps: list = None, api_key: str = None) -> dict:
    """
    Renders the Extraction Review panel on screen as per specification.
    Returns approved dict with chosen title and selected facts.
    """
    st.markdown("### 🔍 AI Director — Script Extraction Review")

    if "extraction_data" not in st.session_state or st.session_state.get("re_extract_requested"):
        with st.spinner("🧠 Analyzing script for high-CTR title & traceable facts..."):
            extracted = extract_title_and_facts(script_text, api_key=api_key)
            extracted["facts"] = auto_align_facts_to_timeline(extracted.get("facts", []), word_timestamps)
            st.session_state["extraction_data"] = extracted
            st.session_state["re_extract_requested"] = False

    data = st.session_state.get("extraction_data", {})
    main_title = data.get("title", "Untitled Story").strip()
    backup_titles = data.get("title_alt", [])
    facts = data.get("facts", [])
    facts = auto_align_facts_to_timeline(facts, word_timestamps)

    # ── 1. TOP SECTION — TITLE ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎬 Proposed Video Title")

    col_title, col_count = st.columns([4, 1])
    with col_title:
        title_input = st.text_input("Title (Title Case):", value=main_title)
    with col_count:
        char_len = len(title_input)
        if char_len <= 60:
            st.markdown(f"**Length:** `{char_len} / 60` 🟢")
        else:
            st.markdown(f"**Length:** `{char_len} / 60` 🔴 *(Over 60 chars)*")

    if backup_titles:
        with st.expander("💡 Other Title Ideas (Click to Swap)", expanded=False):
            for i, alt in enumerate(backup_titles, 1):
                if st.button(f"Option {i}: {alt}", key=f"btn_title_alt_{i}_{abs(hash(alt)) % 10000}", use_container_width=True):
                    st.session_state["extraction_data"]["title"] = alt
                    st.rerun()

    # ── 2. BOTTOM SECTION — EDITABLE FACT & CARD MANAGER PANEL ───────────────
    st.markdown("---")
    col_fh, col_fa = st.columns([3, 1])
    with col_fh:
        st.markdown(f"#### 📊 Editable Fact & Card Manager Panel ({len(facts)} Items)")
    with col_fa:
        if st.button("➕ Add Custom Fact", key="btn_add_custom_fact", use_container_width=True):
            facts.append({
                "text": "Light travels at 299,792 km/s in a vacuum.",
                "confidence": "high",
                "category": "STATISTIC",
                "card_style": "💬 Styled Text Only (No Box)",
                "start_sec": float(len(facts) * 3.5),
                "display_duration": 2.5
            })
            st.session_state["extraction_data"]["facts"] = facts
            st.rerun()

    if not facts:
        st.info("ℹ️ No facts currently extracted. Click '➕ Add Custom Fact' above to create one!")
    else:
        for idx, fact in enumerate(facts, 1):
            f_text = fact.get("text", "").strip()
            confidence = str(fact.get("confidence", "high")).lower()
            category = str(fact.get("category", "other")).upper()

            if confidence == "high":
                conf_badge = "🟢 **HIGH CONFIDENCE**"
            elif confidence == "medium":
                conf_badge = "🟡 **MEDIUM CONFIDENCE**"
            else:
                conf_badge = "🔴 **LOW CONFIDENCE**"

            with st.expander(f"📌 Fact #{idx}: {f_text[:40]}...", expanded=(idx == 1)):
                st.markdown(f"{conf_badge} &nbsp;|&nbsp; `🏷️ {category}`")
                
                # Edit Fact Text
                edited_text = st.text_input(
                    "✏️ Edit Fact Text:",
                    value=f_text,
                    key=f"edit_fact_text_{idx}_{abs(hash(f_text)) % 10000}"
                )
                fact["text"] = edited_text

                # Per-Fact Card Style & Timing Controls
                col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
                with col_sel1:
                    card_style = st.selectbox(
                        "🎨 Card Display Style:",
                        [
                            "💬 Styled Text Only (No Box)",
                            "📊 Infographic Stat Box (Glassmorphism)",
                            "📖 Chapter Header Card (Bracket Frame)",
                            "🎬 Holographic HUD Card",
                            "🍿 Viral Neon Stat Callout",
                            "⚡ Lower Third Pill",
                            "🔥 Cinema Split Screen Card",
                            "🚫 Hide Fact Card",
                        ],
                        index=0,
                        key=f"fact_style_sel_{idx}_{abs(hash(edited_text)) % 10000}",
                    )
                    fact["card_style"] = card_style

                with col_sel2:
                    start_sec = st.number_input(
                        "⏱️ Start (sec):",
                        min_value=0.0,
                        max_value=300.0,
                        value=float(fact.get("start_sec", (idx - 1) * 4.0)),
                        step=0.5,
                        key=f"fact_start_sec_{idx}_{abs(hash(edited_text)) % 10000}",
                    )
                    fact["start_sec"] = start_sec

                with col_sel3:
                    dur_sec = st.number_input(
                        "⌛ Duration (sec):",
                        min_value=1.0,
                        max_value=10.0,
                        value=float(fact.get("display_duration", 2.5)),
                        step=0.5,
                        key=f"fact_dur_sec_{idx}_{abs(hash(edited_text)) % 10000}",
                    )
                    fact["display_duration"] = dur_sec

                # Advanced Per-Fact Typography & Animation Controls
                with st.expander(f"⚙️ Advanced Font, Color & Motion Overrides (Fact #{idx})", expanded=False):
                    col_adv1, col_adv2 = st.columns(2)
                    with col_adv1:
                        fact_font = st.selectbox(
                            "🔤 Font Family:",
                            [
                                "🍿 DejaVu Sans Bold (Default)",
                                "💥 Impact (Heavy Viral Bold)",
                                "🅰️ Arial Black (Modern Bold)",
                                "⚡ Trebuchet (Kinetic Dynamic)",
                                "📖 Georgia (Cinematic Serif)",
                                "✨ Verdana (Clean Ultra-Readable)",
                                "🔹 Tahoma (Crisp Tech)",
                                "📱 Segoe UI (Modern UI)",
                            ],
                            index=0,
                            key=f"fact_font_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["font_family"] = fact_font

                        fact_font_scale = st.slider(
                            "📐 Font Scale:",
                            0.5, 2.5, float(fact.get("font_scale", 1.0)), 0.1,
                            key=f"fact_scale_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["font_scale"] = fact_font_scale

                        fact_fill_style = st.selectbox(
                            "🎨 Fill Style:",
                            ["solid", "gradient"],
                            index=0 if fact.get("fill_style") != "gradient" else 1,
                            key=f"fact_fill_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["fill_style"] = fact_fill_style

                    with col_adv2:
                        fact_color = st.color_picker(
                            "🎨 Text Color:",
                            fact.get("color", "#FFFFFF"),
                            key=f"fact_color_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["color"] = fact_color

                        fact_anim = st.selectbox(
                            "✨ Entrance Motion:",
                            ["tracking", "fade", "slide_up", "slide_down", "slide_left", "slide_right", "word_reveal", "typewriter"],
                            index=0,
                            key=f"fact_anim_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["entrance_animation"] = fact_anim

                        fact_pos = st.selectbox(
                            "📍 Position Anchor:",
                            ["bottom", "top", "center", "lower_third", "upper_third"],
                            index=0,
                            key=f"fact_pos_{idx}_{abs(hash(edited_text)) % 10000}"
                        )
                        fact["position"] = fact_pos

                # Compact Per-Fact Live Preview Canvas (Small & Sleek)
                col_pv_canvas, col_pv_meta = st.columns([1.2, 1])
                with col_pv_canvas:
                    try:
                        w_pv, h_pv = 480, 270
                        bg_pv = np.zeros((h_pv, w_pv, 3), dtype=np.uint8)
                        bg_pv[:, :] = (20, 30, 45)

                        f_cfg = {
                            "fact_text": edited_text,
                            "fact_font_family": fact.get("font_family", "DejaVuSans-Bold.ttf"),
                            "fact_font_scale": fact.get("font_scale", 1.0),
                            "fill_style": fact.get("fill_style", "solid"),
                            "fact_color": fact.get("color", "#FFFFFF"),
                            "fact_position": fact.get("position", "bottom"),
                            "entrance_animation": fact.get("entrance_animation", "tracking"),
                            "display_duration": dur_sec
                        }

                        if "text only" in card_style.lower():
                            from modules.fact_text_overlay import apply_fact_text_overlay
                            pv_frame = apply_fact_text_overlay(bg_pv, 0.8, dur_sec, f_cfg)
                        elif "stat box" in card_style.lower() or "infographic" in card_style.lower():
                            from modules.subtitle_vfx import draw_fact_card_overlay
                            pv_frame = draw_fact_card_overlay(bg_pv, {"label": category, "value": edited_text}, t=0.8, duration=dur_sec)
                        elif "chapter" in card_style.lower():
                            from modules.title_overlay import apply_chapter_overlay
                            pv_frame = apply_chapter_overlay(bg_pv, 0.8, edited_text, {})
                        else:
                            from modules.fact_text_overlay import apply_fact_text_overlay
                            pv_frame = apply_fact_text_overlay(bg_pv, 0.8, dur_sec, f_cfg)

                        st.image(pv_frame, caption=f"Live Preview (Fact #{idx})", width=360)
                    except Exception as pe:
                        st.caption(f"Preview notice: {pe}")

                with col_pv_meta:
                    st.markdown(f"**Style:** `{card_style.split(' (')[0]}`")
                    st.markdown(f"**Font:** `{fact.get('font_family', 'DejaVu Sans').split(' (')[0]}`")
                    st.markdown(f"**Timing:** `{start_sec:.1f}s ➔ {start_sec + dur_sec:.1f}s` ({dur_sec:.1f}s)")
                    if st.button(f"🗑️ Delete Fact #{idx}", key=f"btn_del_fact_{idx}_{abs(hash(edited_text)) % 10000}"):
                        facts.pop(idx - 1)
                        st.session_state["extraction_data"]["facts"] = facts
                        st.rerun()

    # ── 3. BOTTOM OF PAGE — ACTION BUTTONS ───────────────────────────────────
    st.markdown("---")
    is_processing = st.session_state.get("is_rendering", False) or st.session_state.get("is_extracting", False)
    col_app, col_re = st.columns([1, 1])

    with col_app:
        btn_label = "⏳ Processing..." if is_processing else "✅ Approve — Looks Good"
        if st.button(btn_label, type="primary", key="btn_approve_review_panel", disabled=is_processing, use_container_width=True):
            # Debounce protection: prevent click if executed < 0.8s ago
            now = time.time()
            if now - st.session_state.get("last_click_time", 0) < 0.8:
                st.warning("⚠️ Action throttled — please wait a moment.")
                return {"title": title_input, "facts": facts, "approved": st.session_state.get("extraction_approved", False)}
            st.session_state["last_click_time"] = now

            st.session_state["approved_title"] = title_input
            st.session_state["approved_facts"] = facts
            st.session_state["extraction_approved"] = True
            st.session_state["is_rendering"] = True
            st.success("✅ Title & Facts Approved! Proceeding to Scene Creation...")
            st.rerun()
            return {"title": title_input, "facts": facts, "approved": True}

    with col_re:
        re_label = "⏳ Re-extracting..." if is_processing else "↩️ Re-extract"
        if st.button(re_label, key="btn_re_extract_review_panel", disabled=is_processing, use_container_width=True):
            now = time.time()
            if now - st.session_state.get("last_click_time", 0) < 0.8:
                st.warning("⚠️ Action throttled — please wait a moment.")
                return {"title": title_input, "facts": facts, "approved": False}
            st.session_state["last_click_time"] = now

            st.session_state["re_extract_requested"] = True
            st.rerun()

    return {"title": title_input, "facts": facts, "approved": st.session_state.get("extraction_approved", False)}
