"""
ui/progress_tracker.py
─────────────────────────────────────────────────────────────────────────────
Live render progress dashboard for Pixelab.

Usage:
    tracker = ProgressTracker(scene_count)
    tracker.init_ui()
    callback = tracker.make_callback()
    # pass callback to build_master_video(... progress_callback=callback)
    tracker.show_result(success, out_path, total_time, scenes)
─────────────────────────────────────────────────────────────────────────────
"""
import streamlit as st


def _fmt_time(seconds: float) -> str:
    """Formats seconds into '2m 05s' string."""
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


class ProgressTracker:
    """Manages the live render progress UI shown during video generation."""

    def __init__(self, scene_count: int):
        self.scene_count = scene_count
        # Placeholders — populated in init_ui()
        self.progress_bar     = None
        self.status_box       = None
        self.done_metric      = None
        self.fail_metric      = None
        self.pend_metric      = None
        self.elapsed_metric   = None
        self.eta_metric       = None
        self.tracker_ph       = None

    # ── Public API ────────────────────────────────────────────

    def init_ui(self):
        """Creates all placeholder widgets. Call once before rendering starts."""
        st.subheader("📡 Live Generation & Render Tracker")
        self.progress_bar = st.progress(0.0)
        self.status_box   = st.info(
            "🤖 Phase 0: AI Director analyzing script with Groq LLM..."
        )

        c1, c2, c3, c4, c5 = st.columns(5)
        self.done_metric    = c1.empty()
        self.fail_metric    = c2.empty()
        self.pend_metric    = c3.empty()
        self.elapsed_metric = c4.empty()
        self.eta_metric     = c5.empty()
        self.tracker_ph     = st.empty()

        self._update_metrics(done=0, failed=0, left=self.scene_count, elapsed=0, eta="—")

    def on_script_ready(self, scene_count: int):
        """Call after AI Director finishes and scenes are generated."""
        self.progress_bar.progress(0.08)
        # Bug 5 fix: use st.success for proper formatting
        self.status_box.success(
            f"✅ Phase 0 Complete! Generated {scene_count} scenes. "
            "Starting Phase 1 — pre-generating all voiceovers..."
        )

    def make_callback(self):
        """Returns the progress_callback function to pass to build_master_video."""
        def on_progress_update(pct, msg, scene_states, elapsed=0):
            self.progress_bar.progress(min(max(pct / 100.0, 0.0), 1.0))
            self.status_box.info(f"⏳ {msg}")

            # Bug 1 fix: count audio-ready + fully complete scenes as "done"
            done_cnt = sum(
                1 for s in scene_states
                if s["overall"] in ("✅ Complete", "🎙️ Audio Ready")
                or "Audio Ready" in s["overall"]
            )
            # Bug 6 fix: also count ⚠️ Audio Missing as a failure
            fail_cnt = sum(
                1 for s in scene_states
                if "❌" in s["overall"]
                or "Failed" in s["overall"]
                or "⚠️" in s["overall"]
            )
            # Bug 2 fix: clamp to prevent negative Left count
            pend_cnt = max(0, len(scene_states) - done_cnt - fail_cnt)

            # Bug 3 fix: extract ETA from msg, keep last known if not present
            eta_str = "—"
            if "ETA:" in msg:
                try:
                    raw = msg.split("ETA:")[-1].strip().split("|")[0].strip()
                    eta_str = raw if raw else "—"
                except Exception:
                    pass

            self._update_metrics(
                done=done_cnt, failed=fail_cnt, left=pend_cnt,
                elapsed=elapsed, eta=eta_str
            )
            self._render_scene_table(scene_states)

        return on_progress_update

    def show_result(self, success: bool, out_path: str, total_time: float, scenes: list):
        """Renders the final success/failure state with download button."""
        if success and out_path:
            self.progress_bar.progress(1.0)
            self.status_box.success(
                f"🎉 **Video rendered successfully!** "
                f"Total time: **{_fmt_time(total_time)}** | "
                f"Scenes: **{len(scenes)}**"
            )
            st.video(out_path)
            with open(out_path, "rb") as f:
                st.download_button(
                    "⬇️ Download Final Video",
                    f,
                    file_name="pixelab_video.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                )
        else:
            self.status_box.error("❌ Rendering failed. Check the terminal logs.")

    # ── Private helpers ───────────────────────────────────────

    def _update_metrics(self, done, failed, left, elapsed, eta):
        self.done_metric.metric("✅ Done",       str(done))
        self.fail_metric.metric("❌ Failed",     str(failed))
        self.pend_metric.metric("⏳ Left",       str(left))
        self.elapsed_metric.metric("⏱️ Elapsed", _fmt_time(elapsed) if elapsed else "0m 00s")
        self.eta_metric.metric("🏁 ETA",         eta)

    def _render_scene_table(self, scene_states):
        with self.tracker_ph.container():
            st.markdown("### 📊 Phase 1 Scene Breakdown & Kinetic Data Callout Dashboard")
            for s in scene_states:
                icon     = s["overall"].split()[0] if s["overall"] else "⏳"
                is_open  = any(
                    kw in s["overall"]
                    for kw in ("In Progress", "Generating", "Downloading")
                )

                start_sec = s.get("start_sec", 0.0)
                end_sec = s.get("end_sec", 3.5)
                dur = max(0.5, end_sec - start_sec)
                time_str = f"({start_sec:.1f}s – {end_sec:.1f}s, {dur:.1f}s)"

                title_str = s.get("chapter_title") or f"PART {s['index']} OVERVIEW"

                header = (
                    f"{icon} Scene {s['index']} {time_str} | 📌 {title_str} — {s['overall']}"
                )
                with st.expander(header, expanded=is_open):
                    c_thumb, c_details = st.columns([1, 3])
                    with c_thumb:
                        if s.get("thumbnail"):
                            st.image(s["thumbnail"], caption=f"Scene {s['index']} Preview", use_container_width=True)
                        else:
                            st.caption("🖼️ Preview ready after download")
                    with c_details:
                        ca, cb, cc = st.columns(3)
                        ca.write(f"🎙️ **Audio**  \n{s['audio_status']}")
                        cb.write(f"🎥 **Video**  \n{s['video_status']}")
                        cc.write(f"🎨 **VFX**    \n{s['vfx_status']}")

                        st.write(f"📜 **Narration:** *\"{s['narration']}\"*")
                        st.caption(f"🔍 **Stock query:** `{s['query']}`")

                        fc = s.get("fact_card")
                        if fc and isinstance(fc, dict):
                            st.info(f"📊 **Kinetic Data Callout (Peak {fc.get('peak_time', 'midway')}):** `{fc.get('label', 'STAT')}: {fc.get('value', '')}`")

                        if s.get("word_ts"):
                            st.caption(f"⚡ **Word Sync:** {len(s['word_ts'])} timestamps aligned")

