# Resume–JD Match Scorer (with Actionable Suggestions)

Takes a resume (PDF) and a job description (text) and returns:
- A **match score** (0–100%) using sentence embeddings + cosine similarity
- A list of **missing skills** (via a curated skill taxonomy + spaCy PhraseMatcher)
- **Ranked, actionable suggestions** on what to change and why, via a rule-based
  priority engine (JD frequency, requirements-section weighting, hard vs. soft skill)

## Status
🚧 Under active development — Phase 0 (setup) complete.

## Architecture

```
Resume PDF ─┐
            ├─► Text Extraction ─► Cleaning ─► Embedding Model ─┐
JD Text    ─┘                                                    ├─► Cosine Similarity ─► Match Score
                                                                   │
            Resume Text ─► Skill Extraction ──────────────────────┤
            JD Text      ─► Skill Extraction + Frequency ─────────┴─► Missing Skills
                                                                              │
                                                                              ▼
                                                          Suggestion Engine (rule-based ranking)
                                                                              │
                                                                              ▼
                                                             Ranked, Explainable Suggestions
```

## Tech stack
Python 3.12 · sentence-transformers (`all-MiniLM-L6-v2`) · spaCy · FastAPI · Streamlit · Docker

## Run locally
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API docs.

## Live demo
_Coming in Phase 7._

## Author
Sai Kiran Kanuri
