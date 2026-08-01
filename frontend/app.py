"""
frontend/app.py

Streamlit UI — a pure HTTP client of the FastAPI backend (backend/main.py).
Custom CSS gives this a polished, card-based look with a light/dark
theme toggle in the top-right corner. Native Streamlit widgets (file
uploader, text area) are explicitly re-themed via data-testid selectors,
since they ship with their own default styling that ignores page-level
background changes otherwise.
"""
import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

PRIORITY_LABELS = {
    "high": "High Priority",
    "medium": "Medium Priority",
    "low": "Low Priority",
}

st.set_page_config(page_title="Resume-JD Match Scorer", page_icon="📄", layout="centered")

if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ---------------------------------------------------------------------------
# Theme palettes — matched to the purple/charcoal design reference
# ---------------------------------------------------------------------------
THEMES = {
    "dark": {
        "bg": "#161616",
        "card_bg": "#1f1f1f",
        "card_border": "#2c2c2c",
        "text": "#f2f2f2",
        "subtext": "#a3a3a3",
        "accent_from": "#a855f7",
        "accent_to": "#9333ea",
        "title": "#f2f2f2",
        "matched": "#22c55e",
        "missing": "#ef4444",
        "high": "#ef4444",
        "medium": "#eab308",
        "low": "#22c55e",
        "toggle_bg": "#1f1f1f",
        "toggle_border": "#2c2c2c",
    },
    "light": {
    "bg": "#f8fafc",
    "card_bg": "#e2e8f0",
    "card_border": "#cbd5e1",
    "text": "#18181b",
    "subtext": "#6b6b70",
    "accent_from": "#a855f7",
    "accent_to": "#9333ea",
    "title": "#18181b",
    "matched": "#16a34a",
    "missing": "#dc2626",
    "high": "#dc2626",
    "medium": "#ca8a04",
    "low": "#16a34a",
    "toggle_bg": "#e2e8f0",
    "toggle_border": "#cbd5e1",
},
}
T = THEMES[st.session_state.theme]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}
.stApp {{
    background: {T['bg']};
}}
p, span, div, label {{ color: {T['text']}; }}

.hero-title {{
    font-size: 2.4rem;
    font-weight: 800;
    color: {T['title']};
    margin-bottom: 0.2rem;
}}
.hero-subtitle {{
    color: {T['subtext']};
    font-size: 1.02rem;
    margin-bottom: 1.6rem;
}}
.section-label {{
    font-weight: 700;
    font-size: 1.08rem;
    color: {T['text']};
    margin: 1.6rem 0 0.6rem 0;
}}
.card {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}}
.pill {{
    display: inline-block;
    padding: 0.35rem 0.9rem;
    border-radius: 999px;
    font-size: 0.86rem;
    font-weight: 600;
    margin: 0.25rem 0.4rem 0.25rem 0;
}}
.pill-matched {{
    background: {T['matched']}1f;
    color: {T['matched']};
    border: 1px solid {T['matched']}55;
}}
.pill-missing {{
    background: {T['missing']}1f;
    color: {T['missing']};
    border: 1px solid {T['missing']}55;
}}
.suggestion-card {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-left: 4px solid;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.7rem;
}}
.suggestion-badge {{
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.15rem 0.6rem;
    border-radius: 999px;
    margin-bottom: 0.4rem;
}}
.suggestion-text {{
    color: {T['text']};
    font-size: 0.95rem;
    line-height: 1.5;
    opacity: 0.92;
}}
div.stButton > button {{
    background: linear-gradient(90deg, {T['accent_from']}, {T['accent_to']});
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 2rem;
    font-weight: 600;
    font-size: 1rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}}
div.stButton > button:hover {{
    transform: translateY(-1px);
    box-shadow: 0 6px 20px {T['accent_from']}55;
}}
.score-wrap {{
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem 0 1.5rem 0;
}}

/* Native widget overrides — file uploader & text area follow our theme too */
[data-testid="stFileUploader"] section {{
    background: {T['card_bg']} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 12px;
}}
[data-testid="stFileUploaderDropzone"] {{
    background: {T['card_bg']} !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {{
    color: {T['text']} !important;
}}
[data-testid="stTextArea"] textarea {{
    background: {T['card_bg']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 12px;
}}
[data-testid="stFileUploader"] button {{
    background: {T['toggle_bg']} !important;
    color: {T['text']} !important;
    border: 1px solid {T['card_border']} !important;
}}
</style>
""", unsafe_allow_html=True)


def render_score_ring(score: int) -> str:
    """Inline SVG circular progress ring for the match score."""
    radius = 70
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - score / 100)

    if score >= 70:
        color = T["low"]
    elif score >= 40:
        color = T["medium"]
    else:
        color = T["high"]

    return f"""
    <div class="score-wrap">
        <svg width="180" height="180" viewBox="0 0 180 180">
            <circle cx="90" cy="90" r="{radius}" fill="none" stroke="{T['card_border']}" stroke-width="14"/>
            <circle cx="90" cy="90" r="{radius}" fill="none" stroke="{color}" stroke-width="14"
                    stroke-linecap="round"
                    stroke-dasharray="{circumference}"
                    stroke-dashoffset="{offset}"
                    transform="rotate(-90 90 90)"/>
            <text x="90" y="98" text-anchor="middle" font-size="36" font-weight="800" fill="{T['text']}">{score}%</text>
        </svg>
    </div>
    """


# ---------------------------------------------------------------------------
# Top row: title (left) + theme toggle (right) — via columns
# ---------------------------------------------------------------------------
top_left, top_right = st.columns([5, 1])
with top_left:
    st.markdown('<div class="hero-title">📄 Resume-JD Match Scorer</div>', unsafe_allow_html=True)
with top_right:
    toggle_label = "🌙 Dark" if st.session_state.theme == "dark" else "☀️ Light"
    if st.button(toggle_label, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()

st.markdown(
    '<div class="hero-subtitle">Upload your resume and paste a job description '
    'to see how well they match, what\'s missing, and what to fix first.</div>',
    unsafe_allow_html=True,
)

resume_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
jd_text = st.text_area("Paste the job description", height=200)

if st.button("Match", type="primary"):
    if not resume_file:
        st.error("Please upload a resume PDF.")
    elif not jd_text.strip():
        st.error("Please paste a job description.")
    else:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/match",
                    files={"resume": (resume_file.name, resume_file.getvalue(), "application/pdf")},
                    data={"jd_text": jd_text},
                    timeout=30,
                )
            except requests.exceptions.ConnectionError:
                st.error("Couldn't reach the backend. Make sure the API server is running.")
                st.stop()

        if response.status_code != 200:
            detail = response.json().get("detail", "Something went wrong.")
            st.error(detail)
            st.stop()

        result = response.json()

        st.markdown(render_score_ring(result["score"]), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-label">✅ Matched Skills</div>', unsafe_allow_html=True)
            if result["matched_skills"]:
                pills = "".join(f'<span class="pill pill-matched">{s}</span>' for s in result["matched_skills"])
                st.markdown(f'<div class="card">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card">None found.</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="section-label">❌ Missing Skills</div>', unsafe_allow_html=True)
            if result["missing_skills"]:
                pills = "".join(f'<span class="pill pill-missing">{s}</span>' for s in result["missing_skills"])
                st.markdown(f'<div class="card">{pills}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card">None — great coverage!</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">💡 Suggestions</div>', unsafe_allow_html=True)
        if result["suggestions"]:
            for suggestion in result["suggestions"]:
                color = T.get(suggestion["priority"], T["subtext"])
                label = PRIORITY_LABELS.get(suggestion["priority"], suggestion["priority"])
                st.markdown(f"""
                <div class="suggestion-card" style="border-left-color: {color};">
                    <span class="suggestion-badge" style="background: {color}22; color: {color};">{label}</span>
                    <div class="suggestion-text">{suggestion['message']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="card">No suggestions — your resume looks well-aligned with this JD!</div>',
                unsafe_allow_html=True,
            )