"""
Workflow orchestration for the AI Study Pack Generator.
Handles all LLM calls, context passing, and error handling.
"""

import json
import time
import streamlit as st
from groq import Groq

import prompts


# =============================================================================
# GROQ CLIENT
# =============================================================================

def get_client() -> Groq:
    """Initialize Groq client from Streamlit secrets."""
    return Groq(api_key=st.secrets["GROQ_API_KEY"])


def _normalize(parsed, key: str):
    """
    LLMs sometimes return a bare list instead of a dict wrapper.
    Wrap it so downstream code can always do result.get(key, []).
    """
    if isinstance(parsed, list):
        return {key: parsed}
    if isinstance(parsed, dict):
        if key in parsed:
            return parsed
        for alias in (key.rstrip("s"), key + "s", "data", "items", "results"):
            if alias in parsed and isinstance(parsed[alias], list):
                return {key: parsed[alias]}
        list_values = [v for v in parsed.values() if isinstance(v, list)]
        if len(list_values) == 1:
            return {key: list_values[0]}
        return parsed
    raise ValueError(f"Unexpected LLM response type: {type(parsed).__name__}")


# =============================================================================
# CORE LLM CALL
# =============================================================================

def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str = "openai/gpt-oss-120b",
    temperature: float = 0.1,
    max_tokens: int = 4000,
    max_retries: int = 3,
    use_json_mode: bool = True,
) -> dict:
    client = get_client()

    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if use_json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = None
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(**kwargs)
            break
        except Exception as e:
            err = str(e)
            is_rate_limit = "413" in err or "rate_limit_exceeded" in err
            is_transient = "500" in err or "502" in err or "503" in err
            if (is_rate_limit or is_transient) and attempt < max_retries - 1:
                wait = 20 * (attempt + 1) if is_rate_limit else 5 * (attempt + 1)
                time.sleep(wait)
                continue
            raise

    finish_reason = response.choices[0].finish_reason
    if finish_reason == "length":
        raise ValueError("LLM response truncated - increase max_tokens.")

    raw = response.choices[0].message.content
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}\n\nRaw:\n{raw[:500]}")


# =============================================================================
# STAGE 1: PLANNING
# =============================================================================

def stage_planning(user_inputs: dict) -> dict:
    """
    Stage 1: Create the study pack outline.
    """
    prompt = prompts.PLANNING_USER.format(
        topic=user_inputs["topic"],
        skill_level=user_inputs["skill_level"],
        study_duration=user_inputs["study_duration"],
        learning_goals=user_inputs["learning_goals"],
    )

    result = call_llm(
        system_prompt=prompts.PLANNING_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
    )

    if isinstance(result, list):
        result = {
            "title": "Study Pack",
            "estimated_hours": 0,
            "sections": result,
            "prerequisites": [],
        }

    result.setdefault("title", "Study Pack")
    result.setdefault("estimated_hours", 0)
    result.setdefault("sections", [])
    result.setdefault("prerequisites", [])
    return result


# =============================================================================
# STAGE 2: CONTENT GENERATION
# =============================================================================

def stage_content(plan: dict, skill_level: str, progress_cb=None) -> dict:
    """
    Stage 2: Generate explanations and examples ONE SECTION AT A TIME.
    Calls progress_cb(done, total, section_title) after each section.
    """
    sections_out = []
    total = len(plan.get("sections", []))
    done = 0

    for s in plan.get("sections", []):
        section_spec = {
            "id": s["id"],
            "title": s["title"],
            "description": s.get("description", ""),
            "learning_objectives": s.get("learning_objectives", []),
        }

        prompt = prompts.CONTENT_USER.format(
            plan_structure=json.dumps({"sections": [section_spec]}),
            skill_level=skill_level,
        )

        try:
            result = call_llm(
                system_prompt=prompts.CONTENT_SYSTEM,
                user_prompt=prompt,
                temperature=0.3,
                max_tokens=3000,
            )
            normalized = _normalize(result, "sections")
            for sec in normalized.get("sections", []):
                sections_out.append(sec)
        except Exception as e:
            sections_out.append({
                "id": s["id"],
                "title": s["title"],
                "content": f"[Content generation failed for this section: {e}]",
                "examples": [],
                "key_takeaways": [],
            })

        done += 1
        if progress_cb:
            try:
                progress_cb(done, total, s["title"])
            except Exception:
                pass

    return {"sections": sections_out}


# =============================================================================
# STAGE 3: ASSESSMENT
# =============================================================================

def stage_assessment(content: dict, num_questions: int, skill_level: str, topic: str) -> dict:
    """
    Stage 3: Generate quiz questions.
    """
    content_summary = {
        "sections": [
            {
                "id": s["id"],
                "title": s["title"],
                "key_takeaways": s.get("key_takeaways", []),
            }
            for s in content.get("sections", [])
        ]
    }

    prompt = prompts.ASSESSMENT_USER.format(
        num_questions=num_questions,
        content_summary=json.dumps(content_summary),
        skill_level=skill_level,
        topic=topic,
    )

    result = call_llm(
        system_prompt=prompts.ASSESSMENT_SYSTEM,
        user_prompt=prompt,
        temperature=0.3,
    )
    return _normalize(result, "questions")


# =============================================================================
# STAGE 4: REVIEW
# =============================================================================

def stage_review(plan: dict, content: dict, quiz: dict) -> dict:
    """
    Stage 4: Critique using compact summaries to stay under 8K TPM.
    """
    plan_summary = {
        "title": plan.get("title"),
        "sections": [
            {
                "id": s["id"],
                "title": s["title"],
                "learning_objectives": s.get("learning_objectives", []),
            }
            for s in plan.get("sections", [])
        ],
    }

    content_summary = {
        "sections": [
            {
                "id": s["id"],
                "title": s["title"],
                "key_takeaways": s.get("key_takeaways", []),
                "preview": (s.get("content", "") or "")[:200],
            }
            for s in content.get("sections", [])
        ]
    }

    quiz_summary = {
        "questions": [
            {
                "id": q.get("id"),
                "question": (q.get("question", "") or "")[:120],
                "difficulty": q.get("difficulty"),
                "section_id": q.get("section_id"),
            }
            for q in quiz.get("questions", [])
        ]
    }

    prompt = prompts.REVIEW_USER.format(
        plan=json.dumps(plan_summary),
        content=json.dumps(content_summary),
        quiz=json.dumps(quiz_summary),
    )

    result = call_llm(
        system_prompt=prompts.REVIEW_SYSTEM,
        user_prompt=prompt,
        temperature=0.2,
        max_tokens=2000,
    )

    if isinstance(result, list):
        return {
            "overall_score": 5,
            "strengths": [],
            "gaps": result,
            "improvement_suggestions": [],
        }

    if "gaps" not in result:
        for alias in ("issues", "weaknesses", "problems", "items"):
            if alias in result and isinstance(result[alias], list):
                result["gaps"] = result.pop(alias)
                break
        else:
            result["gaps"] = []

    result.setdefault("overall_score", 5)
    result.setdefault("strengths", [])
    result.setdefault("improvement_suggestions", [])
    return result


# =============================================================================
# STAGE 5: REFINEMENT
# =============================================================================

def stage_refinement(content: dict, review: dict) -> dict:
    """
    Stage 5: Improve flagged sections based on review feedback.
    """
    flagged_ids = set()
    for gap in review.get("gaps", []):
        location = gap.get("location", "")
        if location:
            flagged_ids.add(location)

    if not flagged_ids:
        return {
            "refined_sections": [],
            "refinement_notes": "No issues found. Content is already high quality.",
        }

    content_to_fix = {
        "sections": [
            s for s in content.get("sections", [])
            if s["id"] in flagged_ids
        ]
    }

    prompt = prompts.REFINEMENT_USER.format(
        content_to_fix=json.dumps(content_to_fix),
        gaps=json.dumps(review.get("gaps", [])),
        suggestions=json.dumps(review.get("improvement_suggestions", [])),
    )

    result = call_llm(
        system_prompt=prompts.REFINEMENT_SYSTEM,
        user_prompt=prompt,
        temperature=0.3,
        max_tokens=5000,
    )
    return _normalize(result, "refined_sections")


# =============================================================================
# FULL WORKFLOW ORCHESTRATOR
# =============================================================================

def run_workflow(user_inputs: dict, on_stage=None) -> dict:
    """
    Execute the full 5-stage workflow with progress tracking.

    on_stage(stage_key, status, message=None) is called:
      - with status="running" when a stage starts
      - with status="running" + message="Section 3/11: ..." for sub-progress
      - with status="success" / "failed" / "skipped" when it ends
    """
    def notify(key, status, message=None):
        if on_stage:
            try:
                on_stage(key, status, message)
            except Exception:
                pass  # never let a UI callback break the workflow

    results = {
        "plan": None,
        "content": None,
        "quiz": None,
        "review": None,
        "refinement": None,
        "stage_status": {
            "planning": "pending",
            "content": "pending",
            "assessment": "pending",
            "review": "pending",
            "refinement": "pending",
        },
        "errors": [],
    }

    # ---- STAGE 1: PLANNING ----
    notify("planning", "running")
    try:
        results["plan"] = stage_planning(user_inputs)
        results["stage_status"]["planning"] = "success"
        notify("planning", "success")
    except Exception as e:
        results["stage_status"]["planning"] = "failed"
        results["errors"].append(f"Planning stage failed: {e}")
        notify("planning", "failed")
        return results

    # ---- STAGE 2: CONTENT ----
    notify("content", "running")
    try:
        def content_progress(done, total, title):
            notify(
                "content",
                "running",
                f"Section {done}/{total}: {title}",
            )

        results["content"] = stage_content(
            results["plan"],
            user_inputs["skill_level"],
            progress_cb=content_progress,
        )
        results["stage_status"]["content"] = "success"
        notify("content", "success")
    except Exception as e:
        results["stage_status"]["content"] = "failed"
        results["errors"].append(f"Content generation failed: {e}")
        notify("content", "failed")

    # ---- STAGE 3: ASSESSMENT ----
    if results["content"]:
        notify("assessment", "running")
        try:
            results["quiz"] = stage_assessment(
                results["content"],
                user_inputs["num_questions"],
                user_inputs["skill_level"],
                user_inputs["topic"],
            )
            results["stage_status"]["assessment"] = "success"
            notify("assessment", "success")
        except Exception as e:
            results["stage_status"]["assessment"] = "failed"
            results["errors"].append(f"Assessment generation failed: {e}")
            notify("assessment", "failed")
    else:
        results["stage_status"]["assessment"] = "skipped"
        results["errors"].append("Assessment skipped: no content available")
        notify("assessment", "skipped")

    # ---- STAGE 4: REVIEW ----
    if results["plan"] and results["content"]:
        notify("review", "running")
        try:
            results["review"] = stage_review(
                results["plan"],
                results["content"],
                results["quiz"] or {"questions": []},
            )
            results["stage_status"]["review"] = "success"
            notify("review", "success")
        except Exception as e:
            results["stage_status"]["review"] = "failed"
            results["errors"].append(f"Review failed: {e}")
            notify("review", "failed")
    else:
        results["stage_status"]["review"] = "skipped"
        notify("review", "skipped")

    # ---- STAGE 5: REFINEMENT ----
    if results["content"] and results["review"]:
        notify("refinement", "running")
        try:
            results["refinement"] = stage_refinement(
                results["content"],
                results["review"],
            )
            results["stage_status"]["refinement"] = "success"
            notify("refinement", "success")
        except Exception as e:
            results["stage_status"]["refinement"] = "failed"
            results["errors"].append(f"Refinement failed: {e}")
            notify("refinement", "failed")
    else:
        results["stage_status"]["refinement"] = "skipped"
        notify("refinement", "skipped")

    return results