import json
import os
import re
import time
import uuid
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from docx import Document
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from groq import APIConnectionError, APIStatusError, AuthenticationError, Groq, PermissionDeniedError, RateLimitError
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR.parent / ".env.local")
MODEL_NAME = "all-MiniLM-L6-v2"
GROQ_API_URL = "https://api.groq.com"
GROQ_MODEL_ID = "openai/gpt-oss-120b"
MAX_UPLOAD_BYTES = 12 * 1024 * 1024
MAX_RESUME_CHARS = 40_000
SESSION_TTL_SECONDS = 60 * 60
SKILLS = [
    "python", "java", "c++", "javascript", "typescript", "sql", "nosql", "react",
    "angular", "vue", "machine learning", "deep learning", "nlp",
    "natural language processing", "computer vision", "data analysis", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "aws", "azure", "gcp",
    "docker", "kubernetes", "git", "agile", "scrum", "api", "rest", "fastapi",
    "flask", "html", "css", "excel", "tableau", "power bi",
    "communication", "project management", "leadership", "data visualization",
]
sessions: dict[str, dict] = {}

app = FastAPI(title="Resume Studio", docs_url=None, redoc_url=None)
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@lru_cache(maxsize=1)
def load_job_data():
    jobs = pd.read_csv(BASE_DIR / "Dataset" / "job_title_des.csv")
    embeddings = np.load(BASE_DIR / "job_embeddings.npy")
    required = {"Job Title", "Job Description"}
    if not required.issubset(jobs.columns):
        raise RuntimeError("The jobs CSV must include Job Title and Job Description columns.")
    if len(jobs) != embeddings.shape[0]:
        raise RuntimeError("Job rows and precomputed embeddings have different lengths.")
    return jobs, embeddings


@lru_cache(maxsize=1)
def load_embedding_model():
    return SentenceTransformer(MODEL_NAME)


def extract_resume_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix == ".docx":
            document = Document(BytesIO(content))
            text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        elif suffix == ".txt":
            text = content.decode("utf-8-sig")
        else:
            raise HTTPException(status_code=415, detail="Upload a PDF, DOCX, or TXT resume.")
    except (UnicodeDecodeError, Exception) as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=400, detail="The file could not be read. Try exporting it again.") from exc
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise HTTPException(status_code=422, detail="No selectable text was found. Scanned PDFs need OCR first.")
    return text[:MAX_RESUME_CHARS]


def find_skills(text: str) -> list[str]:
    normalized = text.lower()
    return [skill for skill in SKILLS if re.search(r"(?<!\w)" + re.escape(skill) + r"(?!\w)", normalized)]


def get_session(session_id: str) -> dict:
    stored = sessions.get(session_id)
    if not stored or time.time() - stored["created"] > SESSION_TTL_SECONDS:
        sessions.pop(session_id, None)
        raise HTTPException(status_code=404, detail="This resume session expired. Upload the resume again.")
    return stored


class AIRequest(BaseModel):
    session_id: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(AIRequest):
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)


def ask_ai(messages: list[dict]) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="Groq is not configured. Add a newly rotated key to the ignored .env.local file and restart the app.")
    try:
        completion = Groq(api_key=key, base_url=GROQ_API_URL).chat.completions.create(
            model=GROQ_MODEL_ID,
            messages=messages,
            temperature=1,
            max_completion_tokens=2048,
            top_p=1,
            reasoning_effort="medium",
            stream=False,
            stop=None,
        )
        answer = completion.choices[0].message.content or ""
        if not answer.strip():
            raise HTTPException(status_code=502, detail="Groq returned an empty response. Try again or adjust the prompt.")
        return answer
    except AuthenticationError as exc:
        raise HTTPException(status_code=401, detail="Groq rejected the local API key. Verify the key in .env.local.") from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403, detail="Groq denied this request. Check model access and account permissions.") from exc
    except RateLimitError as exc:
        raise HTTPException(status_code=429, detail="Groq rate limit or account quota reached. Try again later or check billing.") from exc
    except APIStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Groq returned an API error (status {exc.status_code}). Check model access and request settings.") from exc
    except APIConnectionError as exc:
        raise HTTPException(status_code=502, detail="Could not connect to Groq. Check your internet connection and retry.") from exc


@app.get("/api/health")
def health():
    jobs, _ = load_job_data()
    return {"status": "ok", "jobs": len(jobs), "ai_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.post("/api/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Keep the resume file under 12 MB.")
    resume_text = extract_resume_text(file.filename or "resume", content)
    jobs, job_embeddings = load_job_data()
    resume_embedding = load_embedding_model().encode([resume_text])
    if resume_embedding.shape[1] != job_embeddings.shape[1]:
        raise HTTPException(status_code=500, detail="The resume and job embedding models do not match.")
    scores = cosine_similarity(resume_embedding, job_embeddings)[0]
    indices = scores.argsort()[-5:][::-1]
    resume_skills = find_skills(resume_text)
    matches = []
    for index in indices:
        description = str(jobs["Job Description"].iloc[index])
        job_skills = find_skills(description)
        matches.append({
            "title": str(jobs["Job Title"].iloc[index]),
            "description": description[:500],
            "score": round(float(scores[index]) * 100, 1),
            "skills": [skill for skill in resume_skills if skill in job_skills],
        })
    now = time.time()
    expired = [key for key, value in sessions.items() if now - value["created"] > SESSION_TTL_SECONDS]
    for key in expired:
        sessions.pop(key, None)
    while len(sessions) >= 250:
        sessions.pop(next(iter(sessions)))
    session_id = uuid.uuid4().hex
    analysis = {"skills": resume_skills, "matches": matches}
    sessions[session_id] = {"created": now, "resume": resume_text, "analysis": analysis}
    return {"session_id": session_id, "word_count": len(resume_text.split()), **analysis}


@app.post("/api/review")
def review_resume(payload: AIRequest):
    session = get_session(payload.session_id)
    context = json.dumps(session["analysis"], ensure_ascii=False)
    answer = ask_ai([
        {"role": "system", "content": "You are a practical, candid career coach. Review the provided CV and local job-match analysis. Give a concise assessment with strengths, gaps, specific improvements, and a 3-step action plan. Do not invent experience or credentials. Clearly distinguish evidence from suggestions."},
        {"role": "user", "content": f"CV text:\n{session['resume']}\n\nLocal job match analysis:\n{context}"},
    ])
    return {"answer": answer}


@app.post("/api/chat")
def chat_about_resume(payload: ChatRequest):
    session = get_session(payload.session_id)
    system_message = {
        "role": "system",
        "content": "You are a supportive, honest career coach. Answer questions about the candidate's CV using only evidence in the CV and the matching results. Suggest concrete edits when useful, but never make up qualifications. Be clear when the CV does not contain enough information.\n\nCV text:\n"
        + session["resume"]
        + "\n\nJob match analysis:\n"
        + json.dumps(session["analysis"], ensure_ascii=False),
    }
    messages = [system_message]
    messages.extend({"role": item.role, "content": item.content} for item in payload.history[-10:])
    messages.append({"role": "user", "content": payload.message})
    return {"answer": ask_ai(messages)}
