# Resume Studio

Resume Studio matches PDF, DOCX, and TXT resumes to the local job library and offers AI-powered CV feedback through Groq.

## Project structure

- `static/` — the frontend app files.
- `scripts/` — Vercel build script that copies the static app into `dist/`.
- `vercel.json` — deployment settings for Vercel.

The frontend is deployed independently from the backend API. Resume text is sent to the backend for matching and AI review, and the frontend only needs the backend origin in `API_BASE_URL`.

## Deploy the frontend to Vercel

1. Import this repository as a Vercel project.
2. Keep the **Root Directory** as the repository root (this project is already the frontend app).
3. The included `vercel.json` runs `npm run build` and publishes `dist`.
4. Set `API_BASE_URL` in Vercel's Production and Preview environment settings to the backend public origin, for example `https://your-api.onrender.com`, without `/api` or a trailing slash.

The frontend build fails on Vercel if `API_BASE_URL` is missing or is not an HTTP(S) origin.

## Run locally on Windows

Start the backend in one PowerShell window:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.local.example .env.local
notepad .env.local
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Add your Groq key to `backend/.env.local`. Keep that file private and uncommitted.

In a second PowerShell window, build and serve the frontend:

```powershell
Set-Location frontend
$env:API_BASE_URL = "http://127.0.0.1:8000"
npm run build
python -m http.server 5173 --directory dist
```

Open `http://127.0.0.1:5173`. The backend's `CORS_ORIGINS` setting in `backend/.env.local.example` permits this local frontend origin.

## Data and sessions

`backend/Dataset/job_title_des.csv` must contain `Job Title` and `Job Description` columns. `backend/job_embeddings.npy` must contain one `all-MiniLM-L6-v2` embedding per row. `backend/Dataset/Resume.csv` and the research notebook are for local data preparation and are not included in the API Docker image.

Resume sessions are stored in API process memory for up to one hour. Run one API instance unless you replace this store with shared persistence; separate instances do not share sessions. Resume text is held in API memory and sent to Groq only for requested AI actions.
