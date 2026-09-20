"""
AI Study Pack Generator — Streamlit UI.
No business logic here. All LLM calls happen in workflow.py.
All Markdown formatting happens in renderer.py.
"""

import streamlit as st
import json

from workflow import run_workflow
from renderer import study_pack_to_markdown


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="📚",
    layout="wide",
)


# =============================================================================
# SIDEBAR — INPUT FORM
# =============================================================================

st.sidebar.header("📚 Study Pack Configuration")

topic = st.sidebar.text_input(
    "Topic",
    placeholder="e.g., Introduction to Machine Learning",
)

skill_level = st.sidebar.selectbox(
    "Skill Level",
    ["Beginner", "Intermediate", "Advanced"],
)

study_duration = st.sidebar.selectbox(
    "Study Duration",
    ["1 week", "2 weeks", "1 month", "2 months", "3 months"],
)

learning_goals = st.sidebar.text_area(
    "Learning Goals",
    placeholder="e.g., Understand supervised learning, build a simple classifier, evaluate model performance",
    height=100,
)

num_questions = st.sidebar.slider(
    "Number of Quiz Questions",
    min_value=3,
    max_value=15,
    value=8,
)

generate_btn = st.sidebar.button(
    "🚀 Generate Study Pack",
    type="primary",
    use_container_width=True,
)


# =============================================================================
# MAIN AREA — HEADER
# =============================================================================

st.title("📚 AI Study Pack Generator")
st.caption("A multi-stage AI workflow: Plan → Generate → Assess → Review → Refine")


# =============================================================================
# WORKFLOW EXECUTION + PROGRESS DISPLAY
# =============================================================================

if generate_btn:
    # Validate inputs
    if not topic.strip():
        st.error("Please enter a topic.")
        st.stop()
    if not learning_goals.strip():
        st.error("Please enter at least one learning goal.")
        st.stop()

    user_inputs = {
        "topic": topic.strip(),
        "skill_level": skill_level,
        "study_duration": study_duration,
        "learning_goals": learning_goals.strip(),
        "num_questions": num_questions,
    }

    # ---- Run workflow with live per-stage progress ----
    st.subheader("🔄 Workflow Progress")

    stage_names = {
        "planning": "1. Planning — Outline structure",
        "content": "2. Content Generation — Explanations & examples",
        "assessment": "3. Assessment — Quiz questions",
        "review": "4. Review — Gap analysis",
        "refinement": "5. Refinement — Improvements",
    }

    status_icons = {
        "pending": "•",
        "running": "⏳",
        "success": "✅",
        "failed": "❌",
        "skipped": "⏭️",
    }

    # Each stage gets a placeholder for the status line,
    # plus a dedicated progress-bar placeholder (only used by the content stage).
    placeholders = {key: st.empty() for key in stage_names}
    progress_bars = {key: st.empty() for key in stage_names}

    def render_stage(key: str, status: str, message: str | None = None):
        label = stage_names[key]
        icon = status_icons.get(status, "❓")

        if message:
            line = f"{icon} **{label}** — {status.upper()} · _{message}_"
        else:
            line = f"{icon} **{label}** — {status.upper()}"

        placeholders[key].markdown(line)

        # Show a progress bar only when the content stage is running with a message
        if key == "content" and status == "running" and message:
            # message looks like "Section 3/11: JavaScript Fundamentals"
            try:
                frac = message.split("Section ")[1].split("/")
                done = int(frac[0])
                total = int(frac[1].split(":")[0])
                progress_bars[key].progress(
                    done / total,
                    text=f"{done} of {total} sections done",
                )
            except Exception:
                progress_bars[key].empty()
        elif status in ("success", "failed", "skipped"):
            # Clear the bar when the stage finishes
            progress_bars[key].empty()

    # Initial render (all pending)
    for key in stage_names:
        render_stage(key, "pending")

    # Callback passed into workflow — updates a stage's status live
    def on_stage(key: str, status: str, message: str | None = None):
        render_stage(key, status, message)

    # Run the workflow (callback fires as each stage starts / ends / progresses)
    results = run_workflow(user_inputs, on_stage=on_stage)

    # ---- Display errors if any ----
    if results["errors"]:
        st.error("**Workflow Errors:**")
        for err in results["errors"]:
            st.write(f"- {err}")

    st.divider()

    # =================================================================
    # RESULTS DISPLAY
    # =================================================================

    # ---- Plan ----
    if results["plan"]:
        with st.expander("📋 Study Plan Structure", expanded=True):
            plan = results["plan"]
            st.write(f"**Title:** {plan.get('title', 'N/A')}")
            st.write(f"**Estimated Hours:** {plan.get('estimated_hours', 'N/A')}")

            for section in plan.get("sections", []):
                st.markdown(f"**{section['title']}** — {section.get('description', '')}")
                st.caption(
                    f"⏱ {section.get('estimated_minutes', '?')} min | "
                    f"Objectives: {', '.join(section.get('learning_objectives', []))}"
                )

    # ---- Content ----
    if results["content"]:
        with st.expander("📖 Generated Content", expanded=True):
            for section in results["content"].get("sections", []):
                st.markdown(f"### {section['title']}")
                st.markdown(section.get("content", ""))

                for ex in section.get("examples", []):
                    st.info(f"**{ex.get('title', 'Example')}:** {ex.get('body', '')}")

                if section.get("key_takeaways"):
                    st.caption("**Key Takeaways:** " + " • ".join(section["key_takeaways"]))
                st.divider()

    # ---- Quiz ----
    if results["quiz"]:
        with st.expander("📝 Quiz Questions", expanded=False):
            for i, q in enumerate(results["quiz"].get("questions", []), 1):
                st.markdown(f"**Q{i}:** {q['question']}")
                for opt in q.get("options", []):
                    st.write(f"  {opt}")
                st.caption(
                    f"✅ Correct: {q.get('correct_answer', '?')} | "
                    f"Difficulty: {q.get('difficulty', '?')} | "
                    f"Section: {q.get('section_id', '?')}"
                )
                st.caption(f"💡 {q.get('explanation', '')}")
                st.divider()

    # ---- Review ----
    if results["review"]:
        with st.expander("🔍 Review & Critique", expanded=False):
            review = results["review"]
            st.metric("Overall Score", f"{review.get('overall_score', '?')}/10")

            if review.get("strengths"):
                st.markdown("**Strengths:**")
                for s in review["strengths"]:
                    st.write(f"✅ {s}")

            if review.get("gaps"):
                st.markdown("**Gaps Found:**")
                for gap in review["gaps"]:
                    st.warning(
                        f"[{gap.get('severity', '?').upper()}] {gap.get('description', '')} "
                        f"(Location: {gap.get('location', 'general')})"
                    )

            if review.get("improvement_suggestions"):
                st.markdown("**Suggestions:**")
                for s in review["improvement_suggestions"]:
                    st.info(s)

    # ---- Refinement ----
    if results["refinement"]:
        with st.expander("✨ Refinements", expanded=False):
            ref = results["refinement"]
            if ref.get("refinement_notes"):
                st.info(ref["refinement_notes"])

            for section in ref.get("refined_sections", []):
                st.markdown(f"### {section['title']} (Improved)")
                st.markdown(section.get("content", ""))
                st.divider()

    # ---- Markdown preview + downloads ----
    if results["plan"] and results["content"]:
        md_text = study_pack_to_markdown(
            plan=results["plan"],
            content=results["content"],
            quiz=results["quiz"],
            review=results["review"],
            refinement=results["refinement"],
        )

        tab_view, tab_raw = st.tabs(["📄 Rendered Markdown", "📝 Raw Markdown Source"])

        with tab_view:
            st.markdown(md_text)

        with tab_raw:
            st.code(md_text, language="markdown")

        col1, col2 = st.columns(2)

        with col1:
            st.download_button(
                "📥 Download Study Pack (.md)",
                data=md_text,
                file_name=f"study_pack_{topic[:30].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col2:
            st.download_button(
                "📥 Download Study Pack (.json)",
                data=json.dumps(
                    {
                        "plan": results["plan"],
                        "content": results["content"],
                        "quiz": results["quiz"],
                        "review": results["review"],
                        "refinement": results["refinement"],
                    },
                    indent=2,
                ),
                file_name=f"study_pack_{topic[:30].replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

else:
    # Welcome state
    st.info("👈 Configure your study pack in the sidebar and click **Generate Study Pack**.")

    st.markdown(
        """
    ### How it works

    This app runs a **5-stage AI workflow**:

    1. **Planning** — Creates the outline and learning objectives
    2. **Content Generation** — Writes explanations and examples
    3. **Assessment** — Builds quiz questions
    4. **Review** — Critiques the output for gaps
    5. **Refinement** — Improves content based on the review

    Each stage receives only the context it needs from previous stages.
    """
    )