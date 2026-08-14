import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("❌ API Key tidak ditemukan di file .env!")
    exit()

client = genai.Client(api_key=GEMINI_API_KEY)

print("🔍 Memeriksa daftar model yang tersedia...\n")
try:
    for model in client.models.list():
        print(f"📌 {model.name}")
except Exception as e:
    print(f"❌ Error saat mengambil model: {e}")
    