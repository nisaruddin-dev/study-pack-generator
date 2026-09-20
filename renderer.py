"""
Converts study pack JSON into a single well-formatted Markdown document.
Pure presentation — no LLM calls, no workflow logic.
"""

from datetime import datetime


def _section_md(section: dict) -> str:
    """Render one content section as Markdown."""
    lines = [f"## {section.get('title', 'Untitled Section')}", ""]
    lines.append(section.get("content", "").strip())
    lines.append("")

    examples = section.get("examples", [])
    if examples:
        lines.append("### Examples")
        lines.append("")
        for ex in examples:
            lines.append(f"**{ex.get('title', 'Example')}**")
            lines.append("")
            lines.append(ex.get("body", "").strip())
            lines.append("")

    takeaways = section.get("key_takeaways", [])
    if takeaways:
        lines.append("### Key Takeaways")
        lines.append("")
        for t in takeaways:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines)


def _quiz_md(quiz: dict) -> str:
    """Render quiz questions as Markdown."""
    lines = ["## Quiz", ""]
    for i, q in enumerate(quiz.get("questions", []), 1):
        lines.append(f"### Q{i}. {q.get('question', '')}")
        lines.append("")
        for opt in q.get("options", []):
            lines.append(f"- {opt}")
        lines.append("")
        lines.append(f"**Answer:** {q.get('correct_answer', '?')}  ")
        lines.append(f"**Difficulty:** {q.get('difficulty', '?')}  ")
        lines.append(f"**Explanation:** {q.get('explanation', '')}")
        lines.append("")
    return "\n".join(lines)


def _review_md(review: dict) -> str:
    """Render review critique as Markdown."""
    lines = ["## Review & Critique", ""]
    lines.append(f"**Overall Score:** {review.get('overall_score', '?')}/10")
    lines.append("")

    strengths = review.get("strengths", [])
    if strengths:
        lines.append("### Strengths")
        lines.append("")
        for s in strengths:
            lines.append(f"- {s}")
        lines.append("")

    gaps = review.get("gaps", [])
    if gaps:
        lines.append("### Gaps Identified")
        lines.append("")
        for g in gaps:
            severity = g.get("severity", "?").upper()
            lines.append(f"- **[{severity}]** {g.get('description', '')}  ")
            lines.append(f"  _Location:_ `{g.get('location', 'general')}`")
        lines.append("")

    suggestions = review.get("improvement_suggestions", [])
    if suggestions:
        lines.append("### Suggestions")
        lines.append("")
        for s in suggestions:
            lines.append(f"- {s}")
        lines.append("")

    return "\n".join(lines)


def _refinement_md(refinement: dict) -> str:
    """Render refinement output as Markdown."""
    lines = ["## Refinements", ""]
    notes = refinement.get("refinement_notes")
    if notes:
        lines.append(f"> {notes}")
        lines.append("")

    for section in refinement.get("refined_sections", []):
        lines.append(f"### {section.get('title', '')} (Improved)")
        lines.append("")
        lines.append(section.get("content", "").strip())
        lines.append("")
    return "\n".join(lines)


def study_pack_to_markdown(
    plan: dict | None,
    content: dict | None,
    quiz: dict | None,
    review: dict | None,
    refinement: dict | None,
) -> str:
    """
    Combine all stage outputs into one Markdown document.
    Any stage that's None is skipped gracefully.
    """
    parts = []

    # Title block
    title = (plan or {}).get("title", "Study Pack")
    parts.append(f"# {title}")
    parts.append("")
    parts.append(f"_Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    parts.append("")

    # Plan overview
    if plan:
        parts.append("## Study Plan Overview")
        parts.append("")
        hours = plan.get("estimated_hours")
        if hours:
            parts.append(f"**Estimated time:** {hours} hours")
            parts.append("")

        prereqs = plan.get("prerequisites", [])
        if prereqs:
            parts.append("**Prerequisites:**")
            parts.append("")
            for p in prereqs:
                parts.append(f"- {p}")
            parts.append("")

        parts.append("### Sections")
        parts.append("")
        for s in plan.get("sections", []):
            mins = s.get("estimated_minutes", "?")
            parts.append(f"- **{s.get('title', '')}** ({mins} min)  ")
            desc = s.get("description", "")
            if desc:
                parts.append(f"  _{desc}_")
            for obj in s.get("learning_objectives", []):
                parts.append(f"  - Objective: {obj}")
        parts.append("")

    # Content sections
    if content:
        parts.append("---")
        parts.append("")
        parts.append("# Study Content")
        parts.append("")
        for section in content.get("sections", []):
            parts.append(_section_md(section))

    # Quiz
    if quiz:
        parts.append("---")
        parts.append("")
        parts.append(_quiz_md(quiz))

    # Review
    if review:
        parts.append("---")
        parts.append("")
        parts.append(_review_md(review))

    # Refinement
    if refinement:
        parts.append("---")
        parts.append("")
        parts.append(_refinement_md(refinement))

    return "\n".join(parts)


def content_to_markdown(content: dict, title: str = "Study Content") -> str:
    lines = [f"# {title}", ""]
    for section in content.get("sections", []):
        lines.append(_section_md(section))
    return "\n".join(lines)


def quiz_to_markdown(quiz: dict) -> str:
    return _quiz_md(quiz)