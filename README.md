[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://study-pack-generator.streamlit.app/)
# 📚 AI Study Pack Generator

A multi-stage AI workflow that turns a topic, skill level, duration, and learning goals into a complete study pack — plan, explanations, quiz, review, and refinement.

Built with **Streamlit** for the UI and **Groq** (`openai/gpt-oss-120b`) for the LLM.

---
## 🌐 Live Demo

**Try it now:** [study-pack-generator.streamlit.app](https://study-pack-generator.streamlit.app/)

No installation required — enter a topic, pick a skill level, and generate a full study pack in under two minutes.

---
## ✨ What It Does

Enter five inputs and get back a full study pack:

| Input | Example |
|---|---|
| **Topic** | "Full stack in 2026" |
| **Skill level** | Beginner / Intermediate / Advanced |
| **Study duration** | 1 week → 3 months |
| **Learning goals** | "From basics to advanced, I only know HTML and CSS" |
| **Quiz questions** | 3 – 15 |

The output includes a structured plan, written explanations with examples, a graded quiz, a critical review, and an improved version of any weak sections — downloadable as Markdown or JSON.

---

## 🔄 How It Works — The 5-Stage Workflow

Each stage receives **only the minimum context** it needs from the previous one. This keeps prompts small, prevents context bloat, and lets each stage fail independently without killing the pipeline.

```
User Inputs
     │
     ▼
┌──────────────────────────────────────────┐
│ 1. PLANNING                              │
│    Creates the study pack outline:       │
│    sections, objectives, time budget     │
└──────────────────────────────────────────┘
     │ sends: section titles + objectives
     ▼
┌──────────────────────────────────────────┐
│ 2. CONTENT GENERATION                    │
│    Generates explanations + examples     │
│    ONE SECTION AT A TIME                 │
└──────────────────────────────────────────┘
     │ sends: section titles + key takeaways
     ▼
┌──────────────────────────────────────────┐
│ 3. ASSESSMENT                            │
│    Creates quiz questions                │
└──────────────────────────────────────────┘
     │ sends: compact summaries of everything
     ▼
┌──────────────────────────────────────────┐
│ 4. REVIEW                                │
│    Critiques the pack, finds gaps,       │
│    scores it 1–10                        │
└──────────────────────────────────────────┘
     │ sends: ONLY flagged sections + critique
     ▼
┌──────────────────────────────────────────┐
│ 5. REFINEMENT                            │
│    Improves the flagged sections         │
└──────────────────────────────────────────┘
     │
     ▼
Full study pack (Markdown + JSON)
```

The **live progress UI** shows each stage transitioning from `PENDING → RUNNING → SUCCESS`. During Content Generation, a per-section progress bar ticks up (`Section 3/11: ...`) so long runs never look frozen.

---

## 🏗️ Project Structure

```
study-pack-generator/
├── .streamlit/
│   └── secrets.toml          # Local-only — DO NOT commit
├── app.py                    # Streamlit UI only — no business logic
├── workflow.py               # Orchestration, LLM calls, error handling
├── prompts.py                # All prompt templates (strings only)
├── renderer.py               # JSON → Markdown conversion for display
├── requirements.txt
├── README.md
└── .gitignore
```

**Design principles:**
- `app.py` contains **no** LLM calls and **no** business logic — it only renders UI and reacts to workflow callbacks.
- `workflow.py` owns **all** orchestration: LLM invocation, context passing, retries, per-stage error handling.
- `prompts.py` contains **only** strings — no code, no logic.
- `renderer.py` is pure presentation — takes the stage outputs and produces one Markdown document.

---

## 🚀 Run Locally

### 1. Clone and enter the project

```bash
git clone <your-repo-url>
cd study-pack-generator
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your Groq API key

Get a free key at [console.groq.com](https://console.groq.com).

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "gsk_your_actual_key_here"
```

### 5. Run the app

```bash
streamlit run app.py
```

If `streamlit` isn't recognized, use:

```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## ☁️ Deploy to Streamlit Community Cloud

1. **Push your code to GitHub.** Make sure `.streamlit/secrets.toml` is in `.gitignore` — **never commit it**.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repo, branch, and set **Main file path** to `app.py`.
4. Click **Advanced settings → Secrets** and paste:
   ```toml
   GROQ_API_KEY = "gsk_your_actual_key_here"
   ```
5. Click **Deploy**. First build takes ~2 minutes.

Once live, you get a public URL. Regenerating the app after code changes is automatic on push.

---

## ⚙️ Model and Limits

- **Model:** `openai/gpt-oss-120b` (Groq)
- **Groq free tier:** 8,000 tokens per minute. The pipeline is designed to stay well under this:
  - Content generation runs **one section per call** — small requests.
  - Review receives **compact summaries**, not full content.
  - Refinement receives **only flagged sections**.
- If you hit a `413` rate limit, the workflow retries automatically with backoff (20s, 40s, 60s). If it still fails, the stage is marked `FAILED` and downstream stages continue where safe.

For very large study packs (3 months, 15+ sections) on the free tier, the Review stage may occasionally hit the ceiling. Bumping `max_tokens` in `stage_content` and trimming the `preview` field in `stage_review` both help.

---

## 🛠️ Built-in Robustness

- **Per-stage try/except** — a failure in one stage doesn't abort the pipeline. The failed stage is reported by name; safe stages continue.
- **Bare-list normalizer** (`_normalize`) — handles cases where the LLM returns a raw JSON array instead of the expected `{"key": [...]}` wrapper.
- **Retry with backoff** — transient `429`/`413` and `5xx` errors retry automatically.
- **Graceful degradation** — if content generation fails for one section, it's replaced with a placeholder and the pipeline continues. Downstream review/refinement often recover it.

---

## 📄 Output Formats

Both are downloadable from the results page:

- **`.md`** — full study pack as Markdown. Opens cleanly in Obsidian, VS Code, GitHub, Notion, or any Markdown viewer. Includes plan overview, content, quiz, review, and refinements.
- **`.json`** — raw structured output of all five stages. Useful for programmatic reuse or re-importing into other tools.

---

## 📦 Requirements

```
streamlit>=1.30.0
groq>=0.11.0
pydantic>=2.0.0
```

---

## 🔒 Security Note

The API key is **only** read from `st.secrets["GROQ_API_KEY"]`. There is no hard-coded fallback. If the secret is missing, the app will surface a clear error at the first LLM call.

Never commit `.streamlit/secrets.toml`. Your `.gitignore` should include:

```
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
venv/
```

---

## 🗺️ Ideas for Extension

- Export to PDF (Markdown → HTML → PDF via `weasyprint` or similar).
- Persist generated packs to a local SQLite database for re-visiting.
- Add a "Regenerate Section" button per section.
- Support multiple language outputs.
- Add a "difficulty distribution" slider for the quiz.

None are required — the current build is complete and deployable.

---

## 📜 License

MIT — do whatever you want with it.
