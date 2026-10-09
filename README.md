# Resume Studio

Resume Studio matches PDF, DOCX, and TXT resumes to the local job library and offers AI-powered CV feedback through Groq.

## Project structure

- `backend/` — FastAPI API, resume processing, job data, and the Render Docker deployment.
- `frontend/` — static web app and its Vercel build/deployment configuration.

The frontend and API are deployed separately. Resume text is embedded locally by the API and sent to Groq only when the user requests a review or chat reply.

## Deploy the backend to Render

1. Create a Render **Web Service** for this repository and choose **Docker** as the runtime.
2. Set **Root Directory** to `backend`. Render will build `backend/Dockerfile`.
3. Set the health check path to `/api/health`.
4. Add these environment variables:
   - `GROQ_API_KEY` — your Groq key. Store it in Render's environment settings; do not put it in the frontend or commit it.
   - `CORS_ORIGINS` — the exact Vercel site origin, for example `https://your-app.vercel.app`. Add any custom domain or preview origins you want to permit, separated by commas and without trailing slashes.

The API listens on Render's `PORT`. The first resume analysis may take longer while `all-MiniLM-L6-v2` downloads. Allow enough memory for PyTorch and the model (at least 2 GB recommended), and ensure the service can reach Hugging Face.

## Deploy the frontend to Vercel

1. Import this repository as a Vercel project.
2. Set **Root Directory** to `frontend`. Only the frontend directory is used for this deployment; the Python backend and its data are outside the Vercel project root.
3. The included `frontend/vercel.json` builds with `npm run build` and publishes `dist`.
4. Set `API_BASE_URL` in Vercel's Production and Preview environment settings to the Render API's public origin, for example `https://your-api.onrender.com`, without `/api` or a trailing slash.

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
