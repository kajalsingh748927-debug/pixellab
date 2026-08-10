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
import streamlit as st
from modules.ai_director import extract_title_and_facts


def render_extraction_review_panel(script_text: str, api_key: str = None) -> dict:
    """
    Renders the Extraction Review panel on screen as per specification.
    Returns approved dict with chosen title and selected facts.
    """
    st.markdown("### 🔍 AI Director — Script Extraction Review")

    if "extraction_data" not in st.session_state or st.session_state.get("re_extract_requested"):
        with st.spinner("🧠 Analyzing script for high-CTR title & traceable facts..."):
            st.session_state["extraction_data"] = extract_title_and_facts(script_text, api_key=api_key)
            st.session_state["re_extract_requested"] = False

    data = st.session_state.get("extraction_data", {})
    main_title = data.get("title", "Untitled Story").strip()
    backup_titles = data.get("title_alt", [])
    facts = data.get("facts", [])

    # ── 1. TOP SECTION — TITLE ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 🎬 Proposed Video Title")

    col_title, col_count = st.columns([4, 1])
    with col_title:
        title_input = st.text_input("Title (Title Case):", value=main_title, key="extracted_title_input")
    with col_count:
        char_len = len(title_input)
        if char_len <= 60:
            st.markdown(f"**Length:** `{char_len} / 60` 🟢")
        else:
            st.markdown(f"**Length:** `{char_len} / 60` 🔴 *(Over 60 chars)*")

    if backup_titles:
        with st.expander("💡 Other Title Ideas (Click to Swap)", expanded=False):
            for i, alt in enumerate(backup_titles, 1):
                if st.button(f"Option {i}: {alt}", key=f"btn_title_alt_{i}", use_container_width=True):
                    st.session_state["extraction_data"]["title"] = alt
                    st.rerun()

    # ── 2. BOTTOM SECTION — FACTS ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"#### 📊 Extracted Facts & Information ({len(facts)} Found)")

    if not facts:
        st.info("ℹ️ No explicit numerical facts or statistics were extracted from this script.")
    else:
        for idx, fact in enumerate(facts, 1):
            f_text = fact.get("text", "").strip()
            confidence = str(fact.get("confidence", "high")).lower()
            category = str(fact.get("category", "other")).upper()
            snippet = str(fact.get("source_snippet", "")).strip()

            # Confidence Badge Colors: Green = high, Yellow = medium, Red = low
            if confidence == "high":
                conf_badge = "🟢 **HIGH CONFIDENCE**"
            elif confidence == "medium":
                conf_badge = "🟡 **MEDIUM CONFIDENCE**"
            else:
                conf_badge = "🔴 **LOW CONFIDENCE**"

            with st.container():
                st.markdown(f"**{idx}. {f_text}**")
                c1, c2 = st.columns([2, 3])
                with c1:
                    st.markdown(f"{conf_badge} &nbsp;|&nbsp; `🏷️ {category}`")
                with c2:
                    if snippet:
                        st.caption(f"💬 *Source Snippet:* \"{snippet}\"")
                st.markdown("<hr style='margin:4px 0px; border-color:#333;'/>", unsafe_allow_html=True)

    # ── 3. BOTTOM OF PAGE — ACTION BUTTONS ───────────────────────────────────
    st.markdown("---")
    col_app, col_re = st.columns([1, 1])

    with col_app:
        if st.button("✅ Approve — Looks Good", type="primary", use_container_width=True):
            st.session_state["approved_title"] = title_input
            st.session_state["approved_facts"] = facts
            st.session_state["extraction_approved"] = True
            st.success("✅ Title & Facts Approved for Video Production!")
            return {"title": title_input, "facts": facts, "approved": True}

    with col_re:
        if st.button("↩️ Re-extract", use_container_width=True):
            st.session_state["re_extract_requested"] = True
            st.rerun()

    return {"title": title_input, "facts": facts, "approved": st.session_state.get("extraction_approved", False)}
