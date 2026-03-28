import streamlit as st

# ---------------- Page Configuration (FIRST & ONLY ONCE) ----------------
st.set_page_config(
    page_title="Resume Builder & Skill Analyzer",
    layout="wide",
    page_icon="📄"
)

import pandas as pd
from rapidfuzz import fuzz
from utils import extract_text_from_pdf, render_resume_pdf, ai_suggestions, enhance_experience_with_ai
from web_scraper import get_latest_skills
import streamlit.components.v1 as components

# ---------------- Sidebar Settings ----------------
st.sidebar.title("⚙️ Settings")

domain = st.sidebar.selectbox(
    "Choose Domain",
    [
        "Web Development", "Data Science", "Machine Learning",
        "Android Development", "DevOps", "Software Engineering"
    ]
)

threshold = st.sidebar.slider(
    "Skill Match Sensitivity (%)", 60, 100, 80, step=5
)

show_tips = st.sidebar.checkbox("💡 Show Resume Improvement Tips (AI)", value=True)

# Fetch skills
with st.spinner("Fetching latest skills..."):
    live_skills = get_latest_skills(domain)

st.sidebar.markdown("### 📌 Trending Skills")
st.sidebar.markdown(
    " ".join([
        f"<span style='background-color:#e1ecf4; color:#0366d6;"
        f"padding:4px 10px; border-radius:12px; margin:3px'>{s}</span>"
        for s in live_skills
    ]),
    unsafe_allow_html=True,
)

# ---------------- Navigation Tabs ----------------
tab = st.sidebar.radio("Go To", ["🧠 Skill Analyzer", "📄 Resume Builder"])

# ---------------- Helper Functions ----------------
def fuzzy_match(skill, text, threshold=80):
    return fuzz.partial_ratio(skill.lower(), text.lower()) >= threshold

def match_resume_with_skills(text, skills, threshold=80):
    matched = [s for s in skills if fuzzy_match(s, text, threshold)]
    missing = [s for s in skills if s not in matched]
    return matched, missing

def calculate_score(matched, total):
    return round((len(matched) / len(total)) * 100, 2) if total else 0

# ---------------- Skill Analyzer ----------------
if tab == "🧠 Skill Analyzer":
    st.title("🧠 Resume Skill Analyzer")

    uploaded = st.file_uploader("Upload Your Resume", type=["pdf", "txt"])

    if uploaded:
        resume_text = (
            extract_text_from_pdf(uploaded)
            if uploaded.type == "application/pdf"
            else uploaded.read().decode("utf-8")
        )

        matched, missing = match_resume_with_skills(resume_text, live_skills, threshold)
        score = calculate_score(matched, live_skills)

        st.metric("ATS Skill Score", f"{score}%")

        if show_tips:
            with st.expander("💡 AI-Based Resume Improvement Tips"):
                st.markdown(ai_suggestions(missing, domain))

# ---------------- Resume Builder ----------------
elif tab == "📄 Resume Builder":
    st.title("📄 ATS Resume Builder")

    left, right = st.columns([1, 1.2])

    with left:
        with st.form("resume_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            summary = st.text_area("Summary")
            skills = st.text_area("Skills (comma separated)")
            education = st.text_area("Education")
            experience = st.text_area("Experience")
            projects = st.text_area("Projects")
            enhance = st.checkbox("Enhance Experience with AI")
            template_choice = st.selectbox("Choose Template", ["ats", "modern", "creative"])
            submitted = st.form_submit_button("Generate Resume")

    if submitted:
        exp_text = enhance_experience_with_ai(experience) if enhance else experience

        resume_data = {
            "name": name,
            "email": email,
            "phone": phone,
            "summary": summary,
            "skills": skills.split(","),
            "education": education.split("\n"),
            "experience": exp_text.split("\n"),
            "projects": projects.split("\n"),
        }

        with right:
            html_preview = render_resume_pdf(resume_data, template_choice, preview=True)
            components.html(html_preview, height=800, scrolling=True)

            pdf_bytes = render_resume_pdf(resume_data, template_choice, preview=False)
            st.download_button("📥 Download PDF", pdf_bytes, file_name="resume.pdf")
