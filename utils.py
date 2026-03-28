import os
import time
from PyPDF2 import PdfReader
from jinja2 import Environment, FileSystemLoader
import pdfkit
from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors

# ------------------ ENV & GEMINI ------------------
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)

# ------------------ TEMPLATE ENGINE ------------------
env = Environment(loader=FileSystemLoader("templates"))

# ------------------ WKHTMLTOPDF ------------------
config = pdfkit.configuration(
    wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
)

# ------------------ HELPERS ------------------
def _generate_with_retry(prompt, max_retries=3):
    """Safe AI call with fallback (prevents app crash)."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text

        except Exception as e:
            print(f"AI error: {e}")

            # retry only a few times
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                # ✅ FINAL FALLBACK (IMPORTANT)
                return "⚠️ AI suggestions unavailable (quota/model issue)."

# ------------------ PDF TEXT EXTRACTION ------------------
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

# ------------------ AI FUNCTIONS ------------------
def ai_suggestions(missing_skills, domain):
    if not missing_skills:
        return "🎉 Your resume already covers all key skills!"

    prompt = f"""
    You are a resume expert for {domain}.
    Missing skills: {', '.join(missing_skills)}.
    Give 5 resume improvement tips.
    """

    result = _generate_with_retry(prompt)

    # ✅ fallback content if AI fails
    if "⚠️" in result:
        return f"""
        ⚠️ AI unavailable.

        Suggested improvements for {domain}:
        - Add missing skills: {', '.join(missing_skills)}
        - Improve project descriptions
        - Use action verbs
        - Quantify achievements
        - Keep formatting clean
        """

    return result

def enhance_experience_with_ai(text):
    if not text.strip():
        return ""

    prompt = f"Rewrite this resume experience professionally:\n{text}"
    result = _generate_with_retry(prompt)

    if "⚠️" in result:
        return text  # fallback → return original text

    return result

# ------------------ PDF RENDER ------------------
def render_resume_pdf(resume_data, template_choice="ats", preview=False):
    template = env.get_template(f"template_{template_choice}.html")
    html = template.render(resume_data)

    if preview:
        return html

    return pdfkit.from_string(
        html,
        False,
        configuration=config,
        options={"enable-local-file-access": ""}
    )
