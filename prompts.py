"""
All prompt templates for the AI Study Pack Generator.
Each prompt is designed to produce valid JSON output.
"""

# =============================================================================
# STAGE 1: PLANNING
# =============================================================================

PLANNING_SYSTEM = """You are an expert curriculum designer. You create structured study plans.
You must respond ONLY with valid JSON. Do not include any text outside the JSON object."""

PLANNING_USER = """Create a study pack structure for:

Topic: {topic}
Skill Level: {skill_level}
Study Duration: {study_duration}
Learning Goals: {learning_goals}

Return a JSON object with exactly this structure:
{{
  "title": "Catchy title for the study pack",
  "estimated_hours": <number>,
  "sections": [
    {{
      "id": "unique_id",
      "title": "Section title",
      "description": "What this section covers",
      "learning_objectives": ["objective 1", "objective 2"],
      "estimated_minutes": <number>
    }}
  ],
  "prerequisites": ["prereq 1", "prereq 2"]
}}

Ensure sections flow logically from foundational to advanced concepts.
Total estimated time should fit within {study_duration}."""


# =============================================================================
# STAGE 2: CONTENT GENERATION
# =============================================================================

CONTENT_SYSTEM = """You are a skilled educator who explains complex topics clearly.
You must respond ONLY with valid JSON. Do not include any text outside the JSON object."""

CONTENT_USER = """Generate study content for the following sections:

Plan Structure:
{plan_structure}

For each section, create:
1. A clear, engaging explanation appropriate for a {skill_level} learner
2. At least two concrete examples or analogies (described in plain prose — do NOT embed multi-line code)
3. Key takeaways

Return a JSON object:
{{
  "sections": [
    {{
      "id": "matching_section_id",
      "title": "Section title",
      "content": "The full explanation text as plain text. Separate paragraphs with a blank line (two real newlines).",
      "examples": [
        {{"title": "Example title", "body": "Prose description of the example. Do not include code blocks or backslashes."}}
      ],
      "key_takeaways": ["takeaway 1", "takeaway 2"]
    }}
  ]
}}

Keep explanations conversational but accurate. Do NOT include code blocks, backticks, or backslash escapes inside any string value. Use real line breaks in your output — do NOT write \\n as literal characters."""


# =============================================================================
# STAGE 3: ASSESSMENT
# =============================================================================

ASSESSMENT_SYSTEM = """You are an assessment specialist who creates effective quiz questions.
You must respond ONLY with valid JSON. Do not include any text outside the JSON object."""

ASSESSMENT_USER = """Create {num_questions} quiz questions based on:

Content Sections:
{content_summary}

For a {skill_level} learner studying {topic}.

Return a JSON object:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "Question text?",
      "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
      "correct_answer": "A",
      "explanation": "Why this answer is correct",
      "difficulty": "easy|medium|hard",
      "section_id": "which section this tests"
    }}
  ]
}}

Mix difficulty levels. Include explanations for every answer."""


# =============================================================================
# STAGE 4: REVIEW
# =============================================================================

REVIEW_SYSTEM = """You are a critical reviewer who identifies weaknesses in educational content.
Be constructive but thorough. You must respond ONLY with valid JSON."""

REVIEW_USER = """Review this study pack for gaps, errors, and weaknesses:

PLAN:
{plan}

CONTENT:
{content}

QUIZ:
{quiz}

Evaluate:
1. Coverage: Does content address all learning objectives?
2. Accuracy: Are there factual errors or oversimplifications?
3. Assessment: Do quiz questions test the right things?
4. Engagement: Is the content likely to hold attention?
5. Prerequisites: Are assumed knowledge bases appropriate?

Return a JSON object:
{{
  "overall_score": <1-10>,
  "strengths": ["strength 1", "strength 2"],
  "gaps": [
    {{
      "type": "missing_topic|weak_explanation|bad_question|unclear_objective",
      "location": "section_id or question_id",
      "description": "What's missing or wrong",
      "severity": "low|medium|high"
    }}
  ],
  "improvement_suggestions": ["suggestion 1", "suggestion 2"]
}}"""


# =============================================================================
# STAGE 5: REFINEMENT
# =============================================================================

REFINEMENT_SYSTEM = """You are an editor who improves educational content based on feedback.
You must respond ONLY with valid JSON. Do not include any text outside the JSON object."""

REFINEMENT_USER = """Improve the following content based on this review critique:

ORIGINAL CONTENT SECTIONS (only the ones needing fixes):
{content_to_fix}

REVIEW FEEDBACK:
{gaps}

CRITIQUE SUGGESTIONS:
{suggestions}

Return a JSON object with the refined sections:
{{
  "refined_sections": [
    {{
      "id": "section_id",
      "title": "Section title",
      "content": "Improved content text",
      "examples": [
        {{"title": "Example title", "body": "Improved example"}}
      ],
      "key_takeaways": ["updated takeaway"]
    }}
  ],
  "refinement_notes": "Brief summary of what was changed and why"
}}

Only include sections that were flagged in the review or need improvement.
Maintain the original structure and learning objectives."""