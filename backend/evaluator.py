import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Memuat environment variables dari file .env
load_dotenv()

# Inisialisasi Client Gemini (Otomatis membaca GEMINI_API_KEY dari .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY tidak ditemukan di file .env!")

client = genai.Client(api_key=GEMINI_API_KEY)

# Profil Kandidat
CANDIDATE_PROFILE = """
Candidate Profile:
- Experience: 13+ years in tech & IT operations, Pivoting to AI & Automation Engineering.
- Core Skills: Python, n8n Automation Workflows, RAG Architecture, REST APIs, Web Scraping.
- AI Stack: LLMs (Gemini, Groq), Prompt Engineering, Vector Search/Embeddings.
- Certifications: IBM Generative AI Engineering, Google Digital Marketing.
- Philosophy: Quality over Quantity, Human-in-the-Loop outreach, Build in Public mindset.
"""

def evaluate_job(job_title: str, job_description: str) -> dict:
    """
    Menganalisis Job Description menggunakan Gemini (SDK v2) dan memberikan keluaran JSON.
    """
    prompt = f"""
    You are an expert AI Technical Recruiter. Evaluate the fit between the following Candidate Profile and Job Posting.

    {CANDIDATE_PROFILE}

    ---
    JOB DETAILS:
    Title: {job_title}
    Description:
    {job_description}

    ---
    INSTRUCTIONS:
    Analyze the alignment rigorously. Return ONLY a valid JSON object with this exact structure:
    {{
        "match_score": <number between 0 and 100>,
        "fit_summary": "<2-3 sentence summary of why candidate fits or doesn't fit>",
        "key_pros": ["<pro1>", "<pro2>"],
        "key_gaps": ["<gap1>", "<gap2>"],
        "recommended_action": "<'Apply Immediately', 'Apply with tailored CV', or 'Skip'>",
        "draft_outreach": "<A personalized, professional 3-sentence outreach pitch highlighting candidate's n8n/AI skills if match >= 70, otherwise empty string>"
    }}
    """

    try:
        # Menggunakan SDK terbaru dan model Gemini 2.5 Flash
        # Ganti model ke gemini-2.0-flash (atau gemini-1.5-flash)
        # Gunakan model gemini-2.5-flash
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)
    except Exception as e:
        return {"error": f"Failed to evaluate job: {str(e)}"}

# Test Sederhana saat script dijalankan langsung
if __name__ == "__main__":
    sample_title = "AI Automation Specialist (Remote)"
    sample_jd = """
    We are looking for a Remote AI Automation Engineer to design workflows using n8n and Python. 
    Requirements: Experience with REST APIs, LLM APIs (Gemini/Groq), and creating custom automated agents. 
    Bonus: Experience with web scraping and building user dashboards.
    """
    print("Testing Evaluator Logic (Gemini SDK v2)...")
    result = evaluate_job(sample_title, sample_jd)
    print(json.dumps(result, indent=2))