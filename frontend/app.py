# Streamlit UI - built in Phase 5
"""
frontend/app.py

Streamlit UI — a pure HTTP client of the FastAPI backend (backend/main.py).
No direct imports from backend/services/; this app only ever talks to
the backend over HTTP, exactly like curl or Swagger did during testing.
This keeps frontend and backend fully decoupled, matching the two-service
deployment plan (Streamlit Cloud + Render) in Section 9 of the project doc.
"""
import os

import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

PRIORITY_BADGES = {
    "high": "🔴 High",
    "medium": "🟡 Medium",
    "low": "🟢 Low",
}

st.set_page_config(page_title="Resume-JD Match Scorer", page_icon="📄")
st.title("📄 Resume-JD Match Scorer")
st.write(
    "Upload your resume and paste a job description to see how well "
    "they match, what's missing, and what to fix first."
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
                st.error(
                    "Couldn't reach the backend. Make sure the API server "
                    "is running."
                )
                st.stop()

        if response.status_code != 200:
            detail = response.json().get("detail", "Something went wrong.")
            st.error(detail)
            st.stop()

        result = response.json()

        st.subheader("Match Score")
        st.metric("Score", f"{result['score']}%")
        st.progress(result["score"] / 100)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✅ Matched Skills")
            if result["matched_skills"]:
                for skill in result["matched_skills"]:
                    st.write(f"- {skill}")
            else:
                st.write("None found.")

        with col2:
            st.subheader("❌ Missing Skills")
            if result["missing_skills"]:
                for skill in result["missing_skills"]:
                    st.write(f"- {skill}")
            else:
                st.write("None — great coverage!")

        st.subheader("💡 Suggestions")
        if result["suggestions"]:
            for suggestion in result["suggestions"]:
                badge = PRIORITY_BADGES.get(suggestion["priority"], suggestion["priority"])
                st.markdown(f"**{badge}** — {suggestion['message']}")
        else:
            st.write("No suggestions — your resume looks well-aligned with this JD!")