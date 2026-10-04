# AI Resume Screener (Elevvo Pathway)

A small Streamlit app that takes an uploaded resume (PDF/DOCX/TXT), extracts text, computes semantic similarity against a jobs dataset using sentence-transformers, and presents the top job matches with visual match cards.

## What this repository contains
- `app.py` — Main Streamlit application.
- `Dataset/job_title_des.csv` — Job titles and descriptions (expected).
- `job_embeddings.npy` — Precomputed job description embeddings (expected).
- `requirements.txt` — Python package list required to run the app.
- `data_prep_visualization.ipynb` — Notebook with data prep / exploration (optional).

## Prerequisites
- Python 3.8+ installed on Windows (add to PATH).
- PowerShell (instructions below assume Windows PowerShell).

## Recommended: create and activate a virtual environment
Open PowerShell in the project folder (`d:\Resume Screen using NLP`) and run:

```powershell
# Resume Studio | Elevvo

A local browser app for matching resumes with the job library and getting AI-powered CV feedback and coaching through Groq.

## Setup on Windows

In PowerShell from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.local.example .env.local
notepad .env.local
```

Paste a newly created Groq key after `GROQ_API_KEY=` in `.env.local`, save, and close Notepad. Do not paste API keys into source code or commit `.env.local`.

Start the app:

```powershell
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. The Groq host (`https://api.groq.com`) and model (`openai/gpt-oss-120b`) are configured in `app.py`; the SDK adds its `/openai/v1/chat/completions` route. The AI status in the sidebar confirms whether the local key was loaded. Restart the app after changing `.env.local`.

## How it works

- Upload a PDF, DOCX, or TXT resume to get the top five semantic matches from the local job library.
- Request a CV review or ask follow-up questions in the coach. Resume text is sent to Groq only for these explicit AI actions.
- The resume is held in server memory for up to one hour and is not written to disk.
- Local job data must include `Dataset/job_title_des.csv` with `Job Title` and `Job Description` columns and a row-aligned `job_embeddings.npy` generated using `all-MiniLM-L6-v2`.
- The embedding model may download the first time a resume is analyzed.

This configuration is intended for local use. Do not expose the development server to a network without adding authentication and HTTPS.

