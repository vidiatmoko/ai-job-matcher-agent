from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.evaluator import evaluate_job

app = FastAPI(
    title="AI Job Matcher API",
    description="API Engine untuk melakukan RAG-based job evaluation & outreach generator",
    version="1.0.0"
)

# Schema request body menggunakan Pydantic
class JobRequest(BaseModel):
    job_title: str
    job_description: str

@app.get("/")
def read_root():
    """Endpoint status check"""
    return {
        "status": "online",
        "service": "AI Job Matcher Engine",
        "version": "1.0.0"
    }

@app.post("/api/evaluate")
def evaluate_job_endpoint(payload: JobRequest):
    """
    Endpoint utama untuk mengevaluasi lowongan kerja.
    Menerima JSON: {"job_title": "...", "job_description": "..."}
    """
    if not payload.job_title.strip() or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="job_title dan job_description tidak boleh kosong.")

    result = evaluate_job(payload.job_title, payload.job_description)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result