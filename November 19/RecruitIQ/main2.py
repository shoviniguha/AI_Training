"""
Enhanced AI Talent Intelligence Platform
Features:
- Multiple CV/JD uploads
- Batch processing with unique IDs
- Ranked candidate lists
- Customizable shortlisting thresholds
- Improved UI with Material Design
- Comprehensive logging
"""

import streamlit as st
import os
import sqlite3
import json
import uuid
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import pandas as pd
import re
from pathlib import Path

# Google GenAI SDK
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIGURATION ====================

DATABASE_PATH = os.getenv("DATABASE_PATH", "hr_recruitment.db")
LOG_FILE = os.getenv("LOG_FILE", "recruitment_system.log")
UPLOAD_FOLDER = "uploaded_files"
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== DATABASE SETUP ====================

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize database with all required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Candidates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                cv_text TEXT,
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)

        # Job descriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_descriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jd_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                filename TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)

        # Candidate rankings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ranking_id TEXT UNIQUE NOT NULL,
                candidate_id TEXT NOT NULL,
                jd_id TEXT NOT NULL,
                match_score REAL,
                skills_matched TEXT,
                skills_gap TEXT,
                strengths TEXT,
                concerns TEXT,
                recommendation TEXT,
                ranking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
                FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id)
            )
        """)

        # Shortlists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shortlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shortlist_id TEXT UNIQUE NOT NULL,
                jd_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                match_score REAL,
                status TEXT DEFAULT 'shortlisted',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id),
                FOREIGN KEY (jd_id) REFERENCES job_descriptions(jd_id)
            )
        """)

        # Processing logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id TEXT UNIQUE NOT NULL,
                process_type TEXT,
                details TEXT,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        logger.info("Database initialized successfully")


# ==================== FILE PROCESSING ====================

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        import io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = []
        for page in reader.pages:
            text.append(page.extract_text() or "")
        return "\n\n".join(text).strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX file."""
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs]).strip()
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT file."""
    try:
        return file_bytes.decode("utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"TXT extraction error: {e}")
        return ""


def extract_text(uploaded_file) -> str:
    """Extract text from uploaded file based on type."""
    file_bytes = uploaded_file.getvalue()
    filename = uploaded_file.name.lower()

    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file_bytes)
    else:
        return extract_text_from_txt(file_bytes)


# ==================== DATABASE OPERATIONS ====================

def save_candidate(filename: str, cv_text: str, file_path: str) -> str:
    """Save candidate to database."""
    candidate_id = f"CAND-{uuid.uuid4().hex[:8].upper()}"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO candidates (candidate_id, filename, cv_text, file_path)
                VALUES (?, ?, ?, ?)
            """, (candidate_id, filename, cv_text, file_path))
            conn.commit()
            logger.info(f"Candidate saved: {candidate_id}")
            return candidate_id
    except Exception as e:
        logger.error(f"Error saving candidate: {e}")
        return None


def save_job_description(title: str, description: str, filename: str = None) -> str:
    """Save job description to database."""
    jd_id = f"JD-{uuid.uuid4().hex[:8].upper()}"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO job_descriptions (jd_id, title, description, filename)
                VALUES (?, ?, ?, ?)
            """, (jd_id, title, description, filename))
            conn.commit()
            logger.info(f"Job description saved: {jd_id}")
            return jd_id
    except Exception as e:
        logger.error(f"Error saving JD: {e}")
        return None


def save_ranking(candidate_id: str, jd_id: str, analysis_result: Dict) -> str:
    """Save ranking result to database."""
    ranking_id = f"RANK-{uuid.uuid4().hex[:8].upper()}"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rankings 
                (ranking_id, candidate_id, jd_id, match_score, skills_matched, 
                 skills_gap, strengths, concerns, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ranking_id,
                candidate_id,
                jd_id,
                analysis_result.get('matchScore', 0),
                json.dumps(analysis_result.get('skillsMatched', [])),
                json.dumps(analysis_result.get('skillsGap', [])),
                json.dumps(analysis_result.get('strengths', [])),
                json.dumps(analysis_result.get('concerns', [])),
                analysis_result.get('recommendation', 'N/A')
            ))
            conn.commit()
            logger.info(f"Ranking saved: {ranking_id}")
            return ranking_id
    except Exception as e:
        logger.error(f"Error saving ranking: {e}")
        return None


def save_shortlist(jd_id: str, candidate_ids: List[str], scores: Dict[str, float]) -> str:
    """Save shortlist to database."""
    shortlist_id = f"SHORT-{uuid.uuid4().hex[:8].upper()}"

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            for candidate_id in candidate_ids:
                cursor.execute("""
                    INSERT INTO shortlists (shortlist_id, jd_id, candidate_id, match_score)
                    VALUES (?, ?, ?, ?)
                """, (shortlist_id, jd_id, candidate_id, scores.get(candidate_id, 0)))
            conn.commit()
            logger.info(f"Shortlist saved: {shortlist_id} with {len(candidate_ids)} candidates")
            return shortlist_id
    except Exception as e:
        logger.error(f"Error saving shortlist: {e}")
        return None


def get_all_candidates() -> List[Dict]:
    """Retrieve all candidates."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM candidates ORDER BY upload_date DESC")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error retrieving candidates: {e}")
        return []


def get_all_job_descriptions() -> List[Dict]:
    """Retrieve all job descriptions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM job_descriptions ORDER BY upload_date DESC")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error retrieving JDs: {e}")
        return []


def get_rankings_by_jd(jd_id: str) -> List[Dict]:
    """Get all rankings for a specific job description."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, c.filename, c.cv_text
                FROM rankings r
                JOIN candidates c ON r.candidate_id = c.candidate_id
                WHERE r.jd_id = ?
                ORDER BY r.match_score DESC
            """, (jd_id,))
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error retrieving rankings: {e}")
        return []


# ==================== AI PROCESSING ====================

def get_genai_client():
    """Initialize Google GenAI client."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


def analyze_candidate(cv_text: str, job_description: str) -> Dict:
    """Analyze candidate CV against job description using AI."""
    try:
        client = get_genai_client()

        prompt = f"""Analyze this CV against the job description and provide a detailed assessment.

CV:
{cv_text}

Job Description:
{job_description}

Respond in JSON format with:
{{
    "matchScore": <number 0-100>,
    "skillsMatched": [<list of matched skills>],
    "skillsGap": [<list of missing skills>],
    "experienceRelevance": "<brief assessment>",
    "recommendation": "<Strong Hire/Good Fit/Potential Fit/Not Recommended>",
    "summary": "<2-3 sentence summary>",
    "strengths": [<list of 3-5 key strengths>],
    "concerns": [<list of 2-4 concerns if any>]
}}

Provide only valid JSON."""

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 1000
            }
        )

        response_text = getattr(response, "text", str(response))

        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            result = json.loads(response_text[json_start:json_end])
            logger.info(f"Analysis completed with score: {result.get('matchScore', 0)}")
            return result
        else:
            logger.error("Failed to parse AI response")
            return {"matchScore": 0, "error": "Failed to parse response"}

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {"matchScore": 0, "error": str(e)}


# ==================== UI COMPONENTS ====================

def render_header():
    """Render application header."""
    st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
            <h1 style="color: white; margin: 0;">🎯 RecruitIQ</h1>
            <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
                Advanced recruitment automation with batch processing & intelligent ranking
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_stats_dashboard():
    """Render statistics dashboard."""
    candidates = get_all_candidates()
    jds = get_all_job_descriptions()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📄 Total CVs", len(candidates))
    with col2:
        st.metric("💼 Active Jobs", len([j for j in jds if j['status'] == 'active']))
    with col3:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rankings")
            total_rankings = cursor.fetchone()[0]
        st.metric("📊 Total Rankings", total_rankings)
    with col4:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(DISTINCT shortlist_id) FROM shortlists")
            total_shortlists = cursor.fetchone()[0]
        st.metric("✅ Shortlists", total_shortlists)


# ==================== STREAMLIT APP ====================

def main():
    st.set_page_config(
        page_title="RecruitIQ",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3rem;
            font-weight: 600;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .warning-box {
            background: #fed7aa;
            border-left: 4px solid #f59e0b;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        .info-box {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Initialize database
    init_database()

    # Render header
    render_header()

    # Sidebar navigation
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
        st.markdown("### Navigation")
        page = st.radio(
            "",
            ["📊 Dashboard", "📤 Upload CVs", "💼 Upload Job Descriptions",
             "🔍 Batch Ranking", "✅ Shortlisting", "⚙️ Settings"],
            label_visibility="collapsed"
        )

        st.markdown("---")
        st.markdown("### Quick Stats")
        render_stats_dashboard()

    # Main content based on selected page
    if page == "📊 Dashboard":
        render_dashboard_page()
    elif page == "📤 Upload CVs":
        render_upload_cvs_page()
    elif page == "💼 Upload Job Descriptions":
        render_upload_jds_page()
    elif page == "🔍 Batch Ranking":
        render_batch_ranking_page()
    elif page == "✅ Shortlisting":
        render_shortlisting_page()
    elif page == "⚙️ Settings":
        render_settings_page()


def render_dashboard_page():
    """Render dashboard page."""
    st.header("📊 Dashboard Overview")

    # Recent activity
    st.subheader("Recent Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 Recent CVs")
        candidates = get_all_candidates()[:5]
        if candidates:
            for candidate in candidates:
                st.markdown(f"""
                    <div class="metric-card">
                        <strong>{candidate['candidate_id']}</strong><br>
                        {candidate['filename']}<br>
                        <small>Uploaded: {candidate['upload_date']}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No CVs uploaded yet")

    with col2:
        st.markdown("### 💼 Recent Job Descriptions")
        jds = get_all_job_descriptions()[:5]
        if jds:
            for jd in jds:
                st.markdown(f"""
                    <div class="metric-card">
                        <strong>{jd['jd_id']}</strong><br>
                        {jd['title']}<br>
                        <small>Created: {jd['upload_date']}</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No job descriptions added yet")


def render_upload_cvs_page():
    """Render CV upload page."""
    st.header("📤 Upload Candidate CVs")

    st.markdown("""
        <div class="info-box">
            📋 <strong>Instructions:</strong> Upload multiple CV files (PDF, DOCX, TXT). 
            Each file will be assigned a unique ID for tracking.
        </div>
    """, unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload CV Files",
        type=['pdf', 'docx', 'txt'],
        accept_multiple_files=True,
        help="Select multiple CV files to upload"
    )

    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} file(s) selected")

        # Preview files
        with st.expander("📁 Preview Selected Files"):
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.size / 1024:.1f} KB)")

        if st.button("🚀 Process and Save CVs", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            results = []

            for idx, file in enumerate(uploaded_files):
                status_text.text(f"Processing {file.name}...")

                # Extract text
                cv_text = extract_text(file)

                if cv_text:
                    # Save file
                    file_path = os.path.join(UPLOAD_FOLDER, file.name)
                    with open(file_path, 'wb') as f:
                        f.write(file.getvalue())

                    # Save to database
                    candidate_id = save_candidate(file.name, cv_text, file_path)

                    if candidate_id:
                        results.append({
                            'filename': file.name,
                            'candidate_id': candidate_id,
                            'status': 'Success'
                        })
                    else:
                        results.append({
                            'filename': file.name,
                            'candidate_id': 'N/A',
                            'status': 'Failed'
                        })
                else:
                    results.append({
                        'filename': file.name,
                        'candidate_id': 'N/A',
                        'status': 'Failed - No text extracted'
                    })

                progress_bar.progress((idx + 1) / len(uploaded_files))

            status_text.text("Processing complete!")

            # Display results
            st.markdown("### 📋 Processing Results")
            df = pd.DataFrame(results)
            st.dataframe(df, use_container_width=True)

            success_count = len([r for r in results if r['status'] == 'Success'])
            st.success(f"✅ Successfully processed {success_count}/{len(uploaded_files)} CVs")


def render_upload_jds_page():
    """Render JD upload page."""
    st.header("💼 Upload Job Descriptions")

    tab1, tab2 = st.tabs(["📝 Manual Entry", "📤 File Upload"])

    with tab1:
        st.subheader("Create Job Description Manually")

        jd_title = st.text_input("Job Title*", placeholder="e.g., Senior Python Developer")
        jd_description = st.text_area(
            "Job Description*",
            height=300,
            placeholder="Paste or type the complete job description..."
        )

        if st.button("💾 Save Job Description", type="primary"):
            if jd_title and jd_description:
                jd_id = save_job_description(jd_title, jd_description)
                if jd_id:
                    st.success(f"✅ Job description saved with ID: {jd_id}")
                    logger.info(f"JD created: {jd_id} - {jd_title}")
                else:
                    st.error("❌ Failed to save job description")
            else:
                st.warning("⚠️ Please fill in all required fields")

    with tab2:
        st.subheader("Upload Job Description Files")

        jd_files = st.file_uploader(
            "Upload JD Files",
            type=['txt', 'pdf', 'docx'],
            accept_multiple_files=True,
            help="Upload multiple job description files"
        )

        if jd_files:
            st.success(f"✅ {len(jd_files)} file(s) selected")

            if st.button("🚀 Process and Save JDs", type="primary"):
                results = []

                for file in jd_files:
                    jd_text = extract_text(file)

                    if jd_text:
                        title = file.name.replace('.txt', '').replace('.pdf', '').replace('.docx', '')
                        jd_id = save_job_description(title, jd_text, file.name)

                        if jd_id:
                            results.append({
                                'filename': file.name,
                                'jd_id': jd_id,
                                'status': 'Success'
                            })
                        else:
                            results.append({
                                'filename': file.name,
                                'jd_id': 'N/A',
                                'status': 'Failed'
                            })
                    else:
                        results.append({
                            'filename': file.name,
                            'jd_id': 'N/A',
                            'status': 'Failed - No text extracted'
                        })

                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)

                success_count = len([r for r in results if r['status'] == 'Success'])
                st.success(f"✅ Successfully processed {success_count}/{len(jd_files)} JDs")


def render_batch_ranking_page():
    """Render batch ranking page."""
    st.header("🔍 Batch Candidate Ranking")

    # Get data
    candidates = get_all_candidates()
    jds = get_all_job_descriptions()

    if not candidates:
        st.warning("⚠️ No candidates available. Please upload CVs first.")
        return

    if not jds:
        st.warning("⚠️ No job descriptions available. Please create a JD first.")
        return

    # Select JD
    st.subheader("1️⃣ Select Job Description")
    jd_options = {f"{jd['jd_id']} - {jd['title']}": jd for jd in jds}
    selected_jd_key = st.selectbox("Choose Job Description", options=list(jd_options.keys()))

    if selected_jd_key:
        selected_jd = jd_options[selected_jd_key]

        with st.expander("📄 View Job Description"):
            st.text_area("", value=selected_jd['description'], height=200, disabled=True)

        st.markdown("---")
        st.subheader("2️⃣ Select Candidates to Rank")

        # Option to select all or specific candidates
        select_all = st.checkbox("Select all candidates", value=True)

        if select_all:
            selected_candidates = candidates
        else:
            candidate_options = {f"{c['candidate_id']} - {c['filename']}": c for c in candidates}
            selected_candidate_keys = st.multiselect(
                "Choose Candidates",
                options=list(candidate_options.keys())
            )
            selected_candidates = [candidate_options[key] for key in selected_candidate_keys]

        st.info(f"📊 {len(selected_candidates)} candidate(s) selected for ranking")

        st.markdown("---")
        st.subheader("3️⃣ Run Ranking")

        if st.button("🚀 Start Batch Ranking", type="primary", disabled=len(selected_candidates) == 0):
            progress_bar = st.progress(0)
            status_text = st.empty()

            ranking_results = []

            for idx, candidate in enumerate(selected_candidates):
                status_text.text(f"Analyzing {candidate['filename']}...")

                # Analyze candidate
                analysis = analyze_candidate(
                    candidate['cv_text'],
                    selected_jd['description']
                )

                # Save ranking
                ranking_id = save_ranking(
                    candidate['candidate_id'],
                    selected_jd['jd_id'],
                    analysis
                )

                ranking_results.append({
                    'candidate_id': candidate['candidate_id'],
                    'filename': candidate['filename'],
                    'match_score': analysis.get('matchScore', 0),

                    'ranking_id': ranking_id
                })

                progress_bar.progress((idx + 1) / len(selected_candidates))

            status_text.text("✅ Ranking complete!")

            # Sort by score
            ranking_results.sort(key=lambda x: x['match_score'], reverse=True)

            # Display results
            st.markdown("### 📊 Ranking Results")

            df = pd.DataFrame(ranking_results)
            st.dataframe(
                df.style.background_gradient(subset=['match_score'], cmap='RdYlGn', vmin=0, vmax=100),
                use_container_width=True
            )

            # Save to session state for shortlisting
            st.session_state['latest_ranking'] = {
                'jd_id': selected_jd['jd_id'],
                'jd_title': selected_jd['title'],
                'results': ranking_results
            }

            st.success("✅ Ranking completed! Go to 'Shortlisting' tab to create shortlist.")


def render_shortlisting_page():
    """Render shortlisting page."""
    st.header("✅ Candidate Shortlisting")

    if 'latest_ranking' not in st.session_state:
        st.info("ℹ️ No recent ranking found. Please run batch ranking first.")

        # Option to view past rankings
        st.markdown("### 📜 View Past Rankings")
        jds = get_all_job_descriptions()
        if jds:
            jd_options = {f"{jd['jd_id']} - {jd['title']}": jd['jd_id'] for jd in jds}
            selected_jd_key = st.selectbox("Select Job Description", options=list(jd_options.keys()))

            if selected_jd_key:
                jd_id = jd_options[selected_jd_key]
                rankings = get_rankings_by_jd(jd_id)

                if rankings:
                    ranking_data = [{
                        'candidate_id': r['candidate_id'],
                        'filename': r['filename'],
                        'match_score': r['match_score'],
                        'recommendation': r['recommendation']
                    } for r in rankings]

                    st.session_state['latest_ranking'] = {
                        'jd_id': jd_id,
                        'jd_title': selected_jd_key.split(' - ')[1],
                        'results': ranking_data
                    }
                    st.rerun()
                else:
                    st.warning("No rankings found for this job description.")
        return

    ranking_data = st.session_state['latest_ranking']

    st.markdown(f"""
        <div class="info-box">
            <strong>Job Description:</strong> {ranking_data['jd_title']}<br>
            <strong>Total Candidates:</strong> {len(ranking_data['results'])}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎯 Set Shortlisting Criteria")

    col1, col2 = st.columns(2)

    with col1:
        criteria_type = st.radio(
            "Shortlisting Method",
            ["By Minimum Score", "By Top N Candidates"],
            help="Choose how to filter candidates"
        )

    with col2:
        if criteria_type == "By Minimum Score":
            min_score = st.slider("Minimum Match Score (%)", 0, 100, 70, 5)
            shortlisted = [r for r in ranking_data['results'] if r['match_score'] >= min_score]
            st.metric("Candidates Meeting Criteria", len(shortlisted))

        elif criteria_type == "By Top N Candidates":
            top_n = st.number_input("Number of Top Candidates", min_value=1, max_value=len(ranking_data['results']),
                                    value=min(10, len(ranking_data['results'])))
            shortlisted = ranking_data['results'][:top_n]
            st.metric("Selected Candidates", len(shortlisted))

    st.markdown("---")

    # Display shortlisted and rejected
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Shortlisted Candidates")
        if shortlisted:
            shortlisted_df = pd.DataFrame(shortlisted)
            st.dataframe(
                shortlisted_df.style.background_gradient(subset=['match_score'], cmap='Greens', vmin=0, vmax=100),
                use_container_width=True
            )

            # Detailed view
            with st.expander("📋 View Detailed Rankings"):
                for candidate in shortlisted:
                    rankings = get_rankings_by_jd(ranking_data['jd_id'])
                    candidate_ranking = next((r for r in rankings if r['candidate_id'] == candidate['candidate_id']),
                                             None)

                    if candidate_ranking:
                        st.markdown(f"#### {candidate['candidate_id']} - {candidate['filename']}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Match Score", f"{candidate['match_score']}%")
                            st.write("**Skills Matched:**")
                            skills = json.loads(candidate_ranking['skills_matched'])
                            for skill in skills[:5]:
                                st.write(f"✅ {skill}")

                        with col_b:

                            st.write("**Skills Gap:**")
                            gaps = json.loads(candidate_ranking['skills_gap'])
                            for gap in gaps[:5]:
                                st.write(f"⚠️ {gap}")

                        st.markdown("---")
        else:
            st.info("No candidates meet the shortlisting criteria")

    with col2:
        st.markdown("### ❌ Not Shortlisted")
        rejected = [r for r in ranking_data['results'] if r not in shortlisted]
        if rejected:
            rejected_df = pd.DataFrame(rejected)
            st.dataframe(
                rejected_df.style.background_gradient(subset=['match_score'], cmap='Reds', vmin=0, vmax=100),
                use_container_width=True
            )
        else:
            st.info("All candidates shortlisted")

    st.markdown("---")

    # Save shortlist


# ==================== UI COMPONENTS ====================

def render_settings_page():
    """Render settings page."""
    st.header("⚙️ Settings & Configuration")

    tab1, tab2 = st.tabs(["🗄️ Database", "🧹 Data Management"])

    with tab1:
        st.subheader("Database Information")

        st.info(f"📁 Database Path: {DATABASE_PATH}")

        # Database statistics
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Table sizes
            tables = ['candidates', 'job_descriptions', 'rankings', 'shortlists', 'processing_logs']
            table_stats = []

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_stats.append({'Table': table, 'Rows': count})

        stats_df = pd.DataFrame(table_stats)
        st.dataframe(stats_df, use_container_width=True)

        st.markdown("---")

        # Database file size
        if os.path.exists(DATABASE_PATH):
            db_size = os.path.getsize(DATABASE_PATH) / (1024 * 1024)  # MB
            st.metric("Database Size", f"{db_size:.2f} MB")

        st.markdown("---")

        # Backup database
        st.subheader("💾 Database Backup")
        if st.button("Create Backup"):
            try:
                backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(DATABASE_PATH, backup_path)
                st.success(f"✅ Backup created: {backup_path}")
                logger.info(f"Database backup created: {backup_path}")
            except Exception as e:
                st.error(f"❌ Backup failed: {str(e)}")
                logger.error(f"Backup error: {e}")

    with tab2:
        st.subheader("🧹 Data Management")

        st.warning("⚠️ Warning: These actions are irreversible!")

        st.markdown("#### Clear Specific Data")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Clear All Rankings", type="secondary"):
                if st.checkbox("Confirm clear rankings"):
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM rankings")
                            conn.commit()
                        st.success("✅ All rankings cleared")
                        logger.info("All rankings cleared")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        with col2:
            if st.button("🗑️ Clear All Shortlists", type="secondary"):
                if st.checkbox("Confirm clear shortlists"):
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM shortlists")
                            conn.commit()
                        st.success("✅ All shortlists cleared")
                        logger.info("All shortlists cleared")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

        st.markdown("---")

        st.markdown("#### Delete Specific Items")

        # Delete candidates
        with st.expander("🗑️ Delete Candidates"):
            candidates = get_all_candidates()
            if candidates:
                candidate_to_delete = st.selectbox(
                    "Select candidate to delete",
                    options=[f"{c['candidate_id']} - {c['filename']}" for c in candidates]
                )

                if st.button("Delete Selected Candidate"):
                    candidate_id = candidate_to_delete.split(' - ')[0]
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM candidates WHERE candidate_id = ?", (candidate_id,))
                            cursor.execute("DELETE FROM rankings WHERE candidate_id = ?", (candidate_id,))
                            cursor.execute("DELETE FROM shortlists WHERE candidate_id = ?", (candidate_id,))
                            conn.commit()
                        st.success(f"✅ Candidate {candidate_id} deleted")
                        logger.info(f"Candidate deleted: {candidate_id}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.info("No candidates to delete")

        # Delete JDs
        with st.expander("🗑️ Delete Job Descriptions"):
            jds = get_all_job_descriptions()
            if jds:
                jd_to_delete = st.selectbox(
                    "Select JD to delete",
                    options=[f"{j['jd_id']} - {j['title']}" for j in jds]
                )

                if st.button("Delete Selected JD"):
                    jd_id = jd_to_delete.split(' - ')[0]
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM job_descriptions WHERE jd_id = ?", (jd_id,))
                            cursor.execute("DELETE FROM rankings WHERE jd_id = ?", (jd_id,))
                            cursor.execute("DELETE FROM shortlists WHERE jd_id = ?", (jd_id,))
                            conn.commit()
                        st.success(f"✅ Job description {jd_id} deleted")
                        logger.info(f"JD deleted: {jd_id}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.info("No job descriptions to delete")

        st.markdown("---")

        st.markdown("#### 🔥 Danger Zone")
        if st.button("⚠️ Reset Entire Database", type="secondary"):
            confirm_reset = st.text_input("Type 'RESET' to confirm:")
            if confirm_reset == "RESET":
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM candidates")
                        cursor.execute("DELETE FROM job_descriptions")
                        cursor.execute("DELETE FROM rankings")
                        cursor.execute("DELETE FROM shortlists")
                        cursor.execute("DELETE FROM processing_logs")
                        conn.commit()
                    st.success("✅ Database reset complete")
                    logger.warning("Database reset performed")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    main()