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
# create venv (one-time)
python -m venv .venv

# activate the venv (every new shell)
.\.venv\Scripts\Activate
```

You should see `(.venv)` at the start of your prompt after activation.

## Install required packages
With the virtual environment active, run:

```powershell
pip install -r .\requirements.txt
```

Notes:
- If `sentence-transformers` installs PyTorch and you prefer CPU-only, pip will install a CPU-compatible wheel automatically in most cases. If you need a specific PyTorch build, follow the instructions at https://pytorch.org.
- After installing packages, download the spaCy English model:

```powershell
python -m spacy download en_core_web_sm
```

## Files you must have
- `Dataset/job_title_des.csv` — make sure this file exists and contains columns `Job Title` and `Job Description`.
- `job_embeddings.npy` — if you don't have precomputed embeddings, you'll need to compute them using the same SentenceTransformer model (`all-MiniLM-L6-v2`) used by the app. See the `data_prep_visualization.ipynb` for hints.

## Run the app (PowerShell)

```powershell
# from project root
.\.venv\Scripts\Activate    # if not already active
streamlit run .\app.py
```

This will open Streamlit in your browser (or show a local URL in the terminal).

## Quick usage
- Upload a resume (PDF/DOCX/TXT) using the file uploader.
- Wait for analysis — the app computes an embedding for the resume and compares it to precomputed job embeddings.
- The top 5 matches are displayed as cards showing a percentage match, job title, a short snippet, and matched skill badges.

## Troubleshooting
- If you see an error about missing `en_core_web_sm`, run: `python -m spacy download en_core_web_sm`.
- If `job_embeddings.npy` is missing, create embeddings using the `sentence-transformers` model and save as `job_embeddings.npy` in the project root.
- If Streamlit fails to start, ensure you're running `streamlit run` from the project directory and that the venv's Python is active.

## Customization
- Colors and small UI tweaks are defined in `app.py` under the branding section — change `PRIMARY`, `ACCENT`, and `BG` variables to adjust look-and-feel.

## License
This repository contains example code. Add a license file if you want to share or publish this project.

---

If you'd like, I can also:
- Pin exact package versions into `requirements.txt` (recommended for reproducibility).
- Add a small script to regenerate `job_embeddings.npy` from `Dataset/job_title_des.csv`.# Data preparation and visualization notebook

This workspace contains a Jupyter notebook `notebooks/data_prep_visualization.ipynb` which:

- Loads CSV datasets from the `Dataset/` folder
- Performs text preprocessing (cleaning, tokenization, stopword removal, lemmatization)
- Runs EDA and visualizations (word counts, wordcloud, n-grams, length distributions)
- Computes TF-IDF, reduces dimensionality (PCA, t-SNE), and visualizes embeddings
- Trains a simple baseline and logistic regression classifier (if a suitable target column exists)
- Saves artifacts (TF-IDF, PCA, model pipeline) to `artifacts/`

How to run

1. Create a Python environment and install dependencies:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. Start JupyterLab or Jupyter Notebook and open `notebooks/data_prep_visualization.ipynb`:

```powershell
jupyter lab
```

Notes

- The notebook auto-detects a text column like `Resume`, `text`, or `description`. If your data uses a different column name, edit the cell that sets `text_col`.
- Outputs (models and vectorizers) are written to `artifacts/` in the project root.
