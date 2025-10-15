import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx
import spacy # <-- BONUS 2: New import

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Resume Screener",
    page_icon="֎🇦🇮",
    layout="centered",
)

# --- BRANDING & COLORS (STATIC) ---
# Static branding values (no sidebar)
company_name = "Elevvo Pathway"
PRIMARY = "#13181B"
ACCENT = "#2AD927"
# Set background to a pleasant blue
BG = "#2269d2"

# Inject polished CSS for header and result cards
st.markdown(f"""
<style>
 :root {{{{ --primary: {PRIMARY}; --accent: {ACCENT}; --bg: {BG}; }}}}
 body, .stApp {{{{ background-color: var(--bg); }}}}
 .app-header {{{{ display:flex; align-items:center; gap:12px; margin-bottom:12px; }}}}
 .app-title {{{{ color: var(--primary); font-weight:800; font-size:32px; letter-spacing:0.2px; }}}}
 .company-name {{{{ color: #344054; font-size:14px; margin-left:6px; opacity:0.9; }}}}
 .top-banner {{{{ padding:10px 14px; border-radius:10px; background:linear-gradient(90deg, rgba(255,255,255,0.9), rgba(255,255,255,0.7)); box-shadow:0 6px 20px rgba(16,24,40,0.06); margin-bottom:16px; }}}}

 /* Result card */
 .match-card {{{{ display:flex; gap:16px; align-items:center; border-radius:14px; padding:14px; margin-bottom:14px; box-shadow:0 8px 24px rgba(16,24,40,0.06); background:linear-gradient(180deg, #ffffff, #fbfdff); }}}}
 .match-left {{{{ width:84px; height:84px; display:flex; align-items:center; justify-content:center; }}}}
 .match-body {{{{ flex:1; }}}}
 .job-title {{{{ font-size:16px; font-weight:700; color:#0f172a; margin-bottom:6px; }}}}
 .job-desc {{{{ color:#475569; font-size:13px; line-height:1.35; }}}}
 .badges {{{{ margin-top:8px; }}}}
 .skill-badge {{{{ display:inline-block; margin:4px 6px 4px 0; padding:6px 10px; border-radius:999px; background:var(--primary); color:#fff; font-size:12px; }}}}
 .score-ring {{{{ width:84px; height:84px; position:relative; }}}}
 .score-text {{{{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center; font-weight:800; color:#dc2626; }}}}

 /* small responsive tweak */
 @media (max-width: 600px) {{{{
     .match-card {{{{ flex-direction:row; }}}}
 }}}}
 </style>
""", unsafe_allow_html=True)

# Top header
# Header/banner removed per request (kept company_name for internal use)


# Function to extract text from different file types
def extract_text_from_file(file):
    text = ""
    if file.type == "application/pdf":
        # Important: Ensure the PDF has selectable text, not just images.
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file.type == "text/plain":
        text = file.read().decode("utf-8")
    return text


try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model not found. In your terminal, please run: 'python -m spacy download en_core_web_sm'")
    nlp = None

# A predefined list of skills (you can expand this list with more skills)
SKILLS_LIST = [
    'python', 'java', 'c++', 'javascript', 'sql', 'nosql', 'react', 'angular', 'vue',
    'machine learning', 'deep learning', 'nlp', 'natural language processing', 'computer vision',
    'data analysis', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
    'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'api', 'rest'
]

def extract_skills(text):
    """Extracts skills from a text using spaCy and a predefined skill list."""
    if not nlp:
        return set()
    
    doc = nlp(text.lower())
    found_skills = set()
    
    # Check for individual words (tokens) that are skills
    for token in doc:
        if token.text in SKILLS_LIST:
            found_skills.add(token.text)
            
    # Check for multi-word skills (noun chunks)
    for chunk in doc.noun_chunks:
        if chunk.text in SKILLS_LIST:
            found_skills.add(chunk.text)
            
    return found_skills
# --- END OF BONUS 2 SETUP ---


# Function to load data and embeddings (cached for performance)
@st.cache_data
def load_data():
    """Loads job data and pre-computed embeddings."""
    try:
        # Adjust the path if your files are in subfolders
        jobs_df = pd.read_csv('Dataset/job_title_des.csv')
        job_embeddings = np.load('job_embeddings.npy')
        return jobs_df, job_embeddings
    except FileNotFoundError:
        st.error("Error: Dataset or embeddings not found. Please ensure 'job_title_des.csv' and 'job_embeddings.npy' are in the correct directory.")
        return None, None

# --- MAIN APP LOGIC ---

st.title("֎🇦🇮 Resume Screener | Elevvo Pathways")
st.write("Upload your resume, and we'll find the best job matches for you from our database!")

# Load data and the NLP model
jobs_df, job_embeddings = load_data()

if jobs_df is not None:
    # Use session state to keep the model loaded, avoiding reloads on every interaction
    if 'model' not in st.session_state:
        with st.spinner("Loading NLP model... This may take a moment."):
            st.session_state.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    model = st.session_state.model
    
    # File uploader for the resume
    uploaded_resume = st.file_uploader("Choose a Resume File (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_resume is not None:
        # Process the file once it's uploaded
        with st.spinner("Analyzing your resume..."):
            resume_text = extract_text_from_file(uploaded_resume)

        if resume_text:
            # Generate embedding for the uploaded resume
            resume_embedding = model.encode([resume_text])

            # Calculate cosine similarity against all job descriptions
            cosine_scores = cosine_similarity(resume_embedding, job_embeddings)[0]

            # Find the top 5 matches
            top_5_indices = cosine_scores.argsort()[-5:][::-1]

            st.success("Analysis complete! Here are your top 5 job matches:")

            # Render attractive result cards
            for i, index in enumerate(top_5_indices):
                job_title = jobs_df['Job Title'].iloc[index]
                job_description = jobs_df['Job Description'].iloc[index]
                match_score = float(cosine_scores[index]) * 100

                # Extract and compare skills
                resume_skills = extract_skills(resume_text)
                job_skills = extract_skills(job_description)
                matching_skills = resume_skills.intersection(job_skills)

                # Determine ring stroke offset for circular progress (SVG circle)
                pct = max(0, min(100, match_score))
                # circle circumference for r=38 -> 2*pi*38
                circ = 2 * 3.14159 * 38
                offset = circ * (1 - pct / 100)

                # Choose color by threshold
                if pct >= 75:
                    ring_color = PRIMARY
                elif pct >= 50:
                    ring_color = ACCENT
                else:
                    ring_color = '#f97316'  # amber-500

                # Build badges HTML
                badges_html = ''
                for s in sorted(list(matching_skills))[:8]:
                    badges_html += f"<span class='skill-badge'>{s.title()}</span>"

                card_html = f"""
                <div class='match-card'>
                  <div class='match-left'>
                    <div class='score-ring'>
                      <svg width='84' height='84'>
                        <defs>
                          <linearGradient id='g{i}' x1='0' x2='1'>
                            <stop offset='0%' stop-color='{ring_color}' stop-opacity='0.95'/>
                            <stop offset='100%' stop-color='{ring_color}' stop-opacity='0.75'/>
                          </linearGradient>
                        </defs>
                        <circle cx='42' cy='42' r='38' stroke='#eef2ff' stroke-width='8' fill='none' />
                        <circle cx='42' cy='42' r='38' stroke='url(#g{i})' stroke-width='8' fill='none' stroke-dasharray='{circ:.2f}' stroke-dashoffset='{offset:.2f}' stroke-linecap='round' transform='rotate(-90 42 42)' />
                      </svg>
                      <div class='score-text'>{pct:.0f}%</div>
                    </div>
                  </div>
                  <div class='match-body'>
                    <div class='job-title'>{i+1}. {job_title} <span style='float:right; font-size:12px; color:#6b7280'>Score: {pct:.2f}%</span></div>
                    <div class='job-desc'>{job_description[:280]}...</div>
                    <div class='badges'>{badges_html}</div>
                  </div>
                </div>
                """

                st.markdown(card_html, unsafe_allow_html=True)
        else:
            st.error("Could not extract text from the uploaded file. Please try a different file or ensure your PDF contains selectable text.")
