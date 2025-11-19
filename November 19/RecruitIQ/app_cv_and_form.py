
# app_cv_and_form.py
from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import os
import io
from datetime import datetime
from typing import Optional
import base64
import json

# optional dependencies for CV parsing
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

try:
    import docx
except Exception:
    docx = None
import uuid

# Database - using SQLite by default, can be changed to PostgreSQL
import sqlite3
from contextlib import contextmanager

# -------------------------
# Database Setup
# -------------------------
DATABASE_PATH = os.getenv("DATABASE_PATH", "applications.db")


def init_database():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            cv_filename TEXT,
            cv_text TEXT,
            communication_style INTEGER,
            work_process INTEGER,
            checkin_frequency INTEGER,
            work_environment INTEGER,
            schedule_structure INTEGER,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_application(application_id: str, cv_filename: str, cv_text: str,
                     culture_responses: dict) -> dict:
    """
    Save application to database.
    Returns dict with status and message.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO applications (
                    application_id, cv_filename, cv_text,
                    communication_style, work_process, checkin_frequency,
                    work_environment, schedule_structure, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                cv_filename,
                cv_text,
                culture_responses.get("communication_style"),
                culture_responses.get("work_process"),
                culture_responses.get("checkin_frequency"),
                culture_responses.get("work_environment"),
                culture_responses.get("schedule_structure"),
                datetime.utcnow().isoformat()
            ))

            conn.commit()

            return {
                "status": "success",
                "message": "Application saved successfully",
                "application_id": application_id,
                "database": DATABASE_PATH
            }

    except sqlite3.IntegrityError:
        return {
            "status": "error",
            "message": "Application ID already exists"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


def get_application(application_id: str) -> Optional[dict]:
    """Retrieve an application by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
            row = cursor.fetchone()

            if row:
                return dict(row)
            return None
    except Exception as e:
        st.error(f"Error retrieving application: {e}")
        return None


def get_all_applications() -> list:
    """Retrieve all applications."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications ORDER BY submitted_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        st.error(f"Error retrieving applications: {e}")
        return []


# -------------------------
# Helper utilities
# -------------------------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    if PyPDF2 is None:
        return "[PyPDF2 not installed: cannot parse PDF here. Install `pip install PyPDF2`]"
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text_pages = []
    for p in reader.pages:
        try:
            text_pages.append(p.extract_text() or "")
        except Exception:
            pass
    return "\n\n".join(text_pages).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    if docx is None:
        return "[python-docx not installed: cannot parse DOCX here. Install `pip install python-docx`]"
    doc = docx.Document(io.BytesIO(file_bytes))
    paras = [p.text for p in doc.paragraphs]
    return "\n".join(paras).strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1", errors="ignore")


def extract_cv_text(uploaded) -> str:
    if uploaded is None:
        return ""
    meta = uploaded.type or ""
    file_bytes = uploaded.getvalue()
    name = uploaded.name.lower()
    if name.endswith(".pdf") or "pdf" in meta:
        return extract_text_from_pdf(file_bytes)
    if name.endswith(".docx") or "msword" in meta or "word" in meta:
        return extract_text_from_docx(file_bytes)
    if name.endswith(".txt") or "text" in meta:
        return extract_text_from_txt(file_bytes)
    return extract_text_from_txt(file_bytes)


def make_download_button(file_bytes: bytes, filename: str, label: str = "Download"):
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{label}</a>'
    return href


# -------------------------
# Initialize Database
# -------------------------
init_database()

# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Upload CV & Culture Questionnaire", layout="wide", page_icon="🧾")

st.markdown(
    """
    <style>
        .card { padding: 1rem; background: white; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
        .slider-label { font-weight: 500; margin-top: 1.5rem; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True
)

# Sidebar for admin view
with st.sidebar:
    st.header("📊 Admin Panel")
    if st.button("View All Applications"):
        st.session_state.show_admin = True
    if st.button("New Application"):
        st.session_state.show_admin = False
        st.session_state.application_id = str(uuid.uuid4())[:8]
        st.rerun()

    st.markdown("---")
    st.caption(f"Database: {DATABASE_PATH}")

    # Search by Application ID
    search_id = st.text_input("Search Application ID")
    if search_id and st.button("Search"):
        app = get_application(search_id)
        if app:
            st.success("Application found!")
            st.json(app)
        else:
            st.error("Application not found")

# Initialize session state
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False
if 'uploaded_cv' not in st.session_state:
    st.session_state.uploaded_cv = None
if 'cv_text' not in st.session_state:
    st.session_state.cv_text = ""
if 'submission_result' not in st.session_state:
    st.session_state.submission_result = None
if 'application_id' not in st.session_state:
    st.session_state.application_id = str(uuid.uuid4())[:8]

# Admin View - Show all applications
if st.session_state.show_admin:
    st.title("📋 All Applications")

    applications = get_all_applications()

    if applications:
        st.write(f"Total Applications: {len(applications)}")

        for app in applications:
            with st.expander(f"Application {app['application_id']} - {app['cv_filename']} ({app['submitted_at']})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("CV Information")
                    st.write(f"**Filename:** {app['cv_filename']}")
                    st.write(f"**Submitted:** {app['submitted_at']}")
                    st.text_area("CV Text", app['cv_text'], height=200, disabled=True, key=f"cv_{app['id']}")

                with col2:
                    st.subheader("Culture Fit Responses")
                    st.metric("Communication Style", app['communication_style'],
                              help="1=Real-time, 5=Async")
                    st.metric("Work Process", app['work_process'],
                              help="1=Collaborative, 5=Independent")
                    st.metric("Check-in Frequency", app['checkin_frequency'],
                              help="1=Daily, 5=Monthly+")
                    st.metric("Work Environment", app['work_environment'],
                              help="1=Office, 5=Remote")
                    st.metric("Schedule Structure", app['schedule_structure'],
                              help="1=Structured, 5=Flexible")
    else:
        st.info("No applications found in database.")

    st.stop()

# Main Application Form
st.title("🧾 Candidate CV Upload & Culture Questionnaire")
st.write("Upload your CV and complete the culture fit questionnaire below.")

st.info(f"Your Application ID: **{st.session_state.application_id}**")

# Layout: two columns
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1) Upload CV")
    uploaded = st.file_uploader("Upload your CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
    if uploaded is not None:
        st.session_state.uploaded_cv = uploaded
        with st.spinner("Extracting text from CV..."):
            cv_text = extract_cv_text(uploaded)
            st.session_state.cv_text = cv_text

        st.success(f"Uploaded: {uploaded.name} ({uploaded.size / 1024:.1f} KB)")
        st.markdown("---")
        st.subheader("CV Preview")
        if st.session_state.cv_text:
            preview = st.session_state.cv_text[:8000]
            st.text_area("Parsed CV Text", value=preview, height=250, disabled=True)
            href = make_download_button(uploaded.getvalue(), uploaded.name, label="📥 Download CV")
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.info("No text could be extracted. Consider uploading a PDF/DOCX with selectable text.")
    else:
        st.info("Please upload a CV to proceed.")

with col2:
    st.header("2) Culture Fit Questionnaire")
    st.write("Rate your preferences on a scale from 1 to 5.")

    st.markdown("---")

    # Question 1
    st.markdown("**Communication Style**")
    st.caption("How comfortable are you working in an environment where most communication happens asynchronously?")
    q1 = st.select_slider(
        "communication_style",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "1 - Prefer real-time",
            2: "2 - Mostly real-time",
            3: "3 - Balanced",
            4: "4 - Mostly async",
            5: "5 - Prefer async"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Question 2
    st.markdown("**Work Process**")
    st.caption("What type of work process do you prefer when completing tasks?")
    q2 = st.select_slider(
        "work_process",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "1 - Highly collaborative",
            2: "2 - Mostly collaborative",
            3: "3 - Balanced",
            4: "4 - Mostly independent",
            5: "5 - Highly independent"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Question 3
    st.markdown("**Check-in Frequency**")
    st.caption("How often do you prefer check-ins and team meetings?")
    q3 = st.select_slider(
        "checkin_frequency",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "1 - Daily",
            2: "2 - Several times/week",
            3: "3 - Weekly",
            4: "4 - Bi-weekly",
            5: "5 - Monthly or less"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Question 4
    st.markdown("**Work Environment**")
    st.caption("What type of work environment do you feel most productive in?")
    q4 = st.select_slider(
        "work_environment",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "1 - Office only",
            2: "2 - Mostly office",
            3: "3 - Hybrid",
            4: "4 - Mostly remote",
            5: "5 - Remote only"
        }[x],
        label_visibility="collapsed"
    )

    st.markdown("---")

    # Question 5
    st.markdown("**Schedule Structure**")
    st.caption("How structured do you prefer your daily work schedule to be?")
    q5 = st.select_slider(
        "schedule_structure",
        options=[1, 2, 3, 4, 5],
        value=3,
        format_func=lambda x: {
            1: "1 - Highly structured",
            2: "2 - Mostly structured",
            3: "3 - Balanced",
            4: "4 - Mostly flexible",
            5: "5 - Highly flexible"
        }[x],
        label_visibility="collapsed"
    )

st.markdown("---")
st.header("3) Submit Application")

if st.button("Submit Application", type="primary", use_container_width=True):
    if not st.session_state.uploaded_cv:
        st.error("Please upload your CV before submitting.")
    else:
        culture_responses = {
            "communication_style": q1,
            "work_process": q2,
            "checkin_frequency": q3,
            "work_environment": q4,
            "schedule_structure": q5
        }

        with st.spinner("Saving your application..."):
            result = save_application(
                application_id=st.session_state.application_id,
                cv_filename=st.session_state.uploaded_cv.name,
                cv_text=st.session_state.cv_text,
                culture_responses=culture_responses
            )
            st.session_state.submission_result = result

        if result.get("status") == "success":
            st.success("✅ Application submitted successfully!")
            st.balloons()
            st.json(result)

            # Option to view submission
            if st.button("View My Submission"):
                app = get_application(st.session_state.application_id)
                if app:
                    st.json(app)
        else:
            st.error(f"❌ Submission failed: {result.get('message')}")

# Footer
st.markdown("---")
with st.expander("⚙️ Settings / Database Info"):
    st.write("**Database Configuration:**")
    st.code(f'DATABASE_PATH={DATABASE_PATH}')
    st.write("**Database Schema:**")
    st.code("""
applications table:
- id (PRIMARY KEY)
- application_id (UNIQUE)
- cv_filename
- cv_text
- communication_style (1-5)
- work_process (1-5)
- checkin_frequency (1-5)
- work_environment (1-5)
- schedule_structure (1-5)
- submitted_at (TIMESTAMP)
- created_at (TIMESTAMP)
    """)
    st.write("To change database location, set DATABASE_PATH environment variable.")
