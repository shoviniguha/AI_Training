# enhanced_streamlit_app.py
"""
RecruitIQ - AI Talent Intelligence Platform
- Home Page with Navigation
- CV Screening & Analysis
- Team Dynamics Prediction & Visualizations
- Interview Question Generator
- Email Notifications (Accept/Reject)
- Complete Logging System
"""

import streamlit as st
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import sqlite3
from contextlib import contextmanager
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, TypedDict
import pandas as pd
import logging
from logging.handlers import RotatingFileHandler
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Import Google GenAI SDK
from google import genai

# LangGraph imports
from langgraph.graph import StateGraph, END

# ==================== LOGGING SETUP ====================

# Create logger
logger = logging.getLogger('RecruitIQ')
logger.setLevel(logging.INFO)

# Prevent adding handlers multiple times
if not logger.hasHandlers():
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler (rotating, max 5MB, 3 backups)
    file_handler = RotatingFileHandler('app.log', maxBytes=5 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

logger.info("🔄 RecruitIQ Application initialized")

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "applications.db")
logger.info(f"Database path: {DATABASE_PATH}")

# Email configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")


# ==================== EMAIL FUNCTIONS ====================

def send_email(recipient_email: str, subject: str, body: str, is_html: bool = True) -> bool:
    """Send email using SMTP with masked sender name."""
    logger.info(f"Attempting to send email to: {recipient_email}")

    if not SENDER_EMAIL or not SENDER_PASSWORD:
        logger.error("Email credentials not configured")
        st.error("⚠️ Email credentials not configured in .env file")
        return False

    try:
        # Create email message
        msg = MIMEMultipart('alternative')

        # 🔥 MASKED SENDER (This is what the candidate will see)
        msg['From'] = "RecruitIQ <RecruitIQ@hr.com>"

        msg['To'] = recipient_email
        msg['Subject'] = subject

        # Attach body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))

        # Gmail SMTP server connection
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # 🔐 Login with REAL credentials (from .env)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # Send the message
        server.send_message(msg)
        server.quit()

        logger.info(f"Email sent successfully to: {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending email to {recipient_email}: {str(e)}", exc_info=True)
        st.error(f"Failed to send email: {str(e)}")
        return False


def send_shortlist_email(candidate_name: str, candidate_email: str, position: str, interview_date: str = None):
    """Send shortlist notification email"""
    subject = "Congratulations"

    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Congratulations!</h1>
            </div>
            <div class="content">
                <h2>You've Been Shortlisted!</h2>
                <p>We are pleased to inform you that your application for the position of <strong>{position}</strong> has been shortlisted.</p>

                <p>Our team was impressed by your qualifications and experience. We would like to move forward with the next steps in our hiring process.</p>

                {f'<p><strong>Tentative Interview Date:</strong> {interview_date}</p>' if interview_date else ''}

                <p><strong>Next Steps:</strong></p>
                <ul>
                    <li>Our HR team will contact you within 2-3 business days</li>
                    <li>We'll schedule a detailed interview</li>
                    <li>Please keep your availability ready</li>
                </ul>

                <p>If you have any questions, feel free to reply to this email.</p>

                <p>Best regards,<br>
                <strong>Hiring Team</strong><br>
                RecruitIQ Platform</p>
            </div>
            <div class="footer">
                <p>This is an automated message from RecruitIQ AI Talent Intelligence Platform</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(candidate_email, subject, body)

def send_rejection_email(candidate_name: str, candidate_email: str, position: str):
    """Send rejection notification email"""
    subject = "Regretted"

    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }}
            .header {{ background: linear-gradient(135deg, #434343 0%, #000000 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: white; padding: 30px; border-radius: 0 0 10px 10px; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Regretted</h1>
            </div>
            <div class="content">
                <p>Dear Candidate,</p>

                <p>Thank you for applying for the position of <strong>{position}</strong>.</p>

                <p>After careful review of your application, we regret to inform you that you were not selected for the next stage of the hiring process.</p>

                <p>We appreciate the effort you put into your application and encourage you to apply for future opportunities that match your skills and experience.</p>

                <p>We wish you the best of luck in your job search and future endeavors.</p>

                <p>Best regards,<br>
                <strong>Hiring Team</strong><br>
                RecruitIQ Platform</p>
            </div>
            <div class="footer">
                <p>This is an automated message from RecruitIQ AI Talent Intelligence Platform</p>
            </div>
        </div>
    </body>
    </html>
    """

    return send_email(candidate_email, subject, body)

# ==================== DATABASE FUNCTIONS ====================

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    logger.debug("Establishing database connection")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        logger.debug("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}", exc_info=True)
        raise
    finally:
        conn.close()
        logger.debug("Database connection closed")


def get_all_applications():
    """Retrieve all applications from database."""
    logger.info("Fetching all applications from database")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications ORDER BY submitted_at DESC")
            rows = cursor.fetchall()
            applications = [dict(row) for row in rows]
            logger.info(f"Retrieved {len(applications)} applications")
            return applications
    except Exception as e:
        logger.error(f"Error retrieving applications: {e}", exc_info=True)
        st.error(f"Error retrieving applications: {e}")
        return []


def get_application(application_id: str):
    """Retrieve an application by ID."""
    logger.info(f"Fetching application with ID: {application_id}")
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
            row = cursor.fetchone()
            if row:
                logger.info(f"Application found: {application_id}")
                return dict(row)
            logger.warning(f"Application not found: {application_id}")
            return None
    except Exception as e:
        logger.error(f"Error retrieving application {application_id}: {e}", exc_info=True)
        st.error(f"Error retrieving application: {e}")
        return None


# ==================== LANGGRAPH STATE ====================

class RecruitmentState(TypedDict):
    """State for the unified recruitment workflow"""
    cv_text: str
    job_description: str
    candidate_profile: Dict[str, int]
    team_profile: Dict[str, int]
    parsed_cv: Dict[str, Any]
    skill_match_score: float
    experience_score: float
    culture_fit_score: float
    overall_score: float
    skills_matched: List[str]
    skills_gap: List[str]
    strengths: List[str]
    concerns: List[str]
    personality_profile: Dict[str, Any]
    team_synergy_score: float
    conflict_risk_areas: List[str]
    collaboration_strengths: List[str]
    interview_questions: List[Dict[str, str]]
    recommendation: str
    hiring_brief: Dict[str, Any]
    stage: str
    errors: List[str]


# ==================== AI CLIENT ====================

def get_genai_client():
    logger.debug("Initializing Gemini API client")
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment variables")
        raise RuntimeError("❌ GOOGLE_API_KEY not found! Set it in your .env file.")
    logger.info("Gemini API client initialized successfully")
    return genai.Client(api_key=api_key)


def call_gemini(prompt: str, model: str = "gemini-2.0-flash-exp",
                max_output_tokens: int = 2000, temperature: float = 0.7) -> str:
    """Call Gemini and return generated text"""
    logger.info(f"Calling Gemini API - Model: {model}, Temperature: {temperature}")

    try:
        client = get_genai_client()
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config={
                "max_output_tokens": max_output_tokens,
                "temperature": temperature
            }
        )
        text = getattr(resp, "text", None)
        if not text:
            text = str(resp)

        logger.info(f"Gemini API response received - Length: {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}", exc_info=True)
        st.error(f"Gemini API error: {str(e)}")
        return "{}"


# ==================== TEAM DYNAMICS NODE ====================

def team_dynamics_prediction_node(state: RecruitmentState) -> RecruitmentState:
    """Predict team dynamics and personality fit"""
    logger.info("Starting team dynamics prediction node")

    candidate = state.get('candidate_profile', {})
    team = state.get('team_profile', {})
    cv_data = state.get('parsed_cv', {})

    prompt = f"""Analyze this candidate's personality and team dynamics potential:

Candidate CV Summary:
{json.dumps(cv_data, indent=2)}

Candidate Work Style Profile:
- Communication: {candidate.get('communication_style', 3)}/5 (1=sync, 5=async)
- Work Process: {candidate.get('work_process', 3)}/5 (1=collaborative, 5=independent)
- Check-ins: {candidate.get('checkin_frequency', 3)}/5 (1=daily, 5=monthly)
- Environment: {candidate.get('work_environment', 3)}/5 (1=office, 5=remote)
- Schedule: {candidate.get('schedule_structure', 3)}/5 (1=structured, 5=flexible)

Team Profile:
- Communication: {team.get('team_communication', 3)}/5
- Work Process: {team.get('team_work_process', 3)}/5
- Check-ins: {team.get('team_checkin_frequency', 3)}/5
- Environment: {team.get('team_work_environment', 3)}/5
- Schedule: {team.get('team_schedule_structure', 3)}/5

Provide detailed JSON analysis:
{{
  "personalityProfile": {{
    "workStyle": "<collaborative/independent/balanced>",
    "communicationStyle": "<direct/thoughtful/adaptive>",
    "decisionMaking": "<quick/deliberate/consultative>",
    "stressResponse": "<resilient/moderate/sensitive>",
    "leadershipPotential": "<high/medium/low>"
  }},
  "teamSynergyScore": <0-100>,
  "conflictRiskAreas": ["list of potential friction points"],
  "collaborationStrengths": ["list of how they'll enhance team"]
}}

Be specific. Valid JSON only."""

    try:
        response_text = call_gemini(prompt, max_output_tokens=2000, temperature=0.7)

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            result = json.loads(response_text[start_idx:end_idx])
            state['personality_profile'] = result.get('personalityProfile', {})
            state['team_synergy_score'] = float(result.get('teamSynergyScore', 0))
            state['conflict_risk_areas'] = result.get('conflictRiskAreas', [])
            state['collaboration_strengths'] = result.get('collaborationStrengths', [])
            state['stage'] = 'team_dynamics_predicted'

            logger.info(f"Team dynamics prediction successful - Synergy score: {state['team_synergy_score']}")
        else:
            logger.warning("Failed to parse team dynamics JSON response")
            state['errors'].append("Failed to parse team dynamics JSON")
    except Exception as e:
        logger.error(f"Team dynamics prediction error: {str(e)}", exc_info=True)
        state['errors'].append(f"Team dynamics error: {str(e)}")

    return state


# ==================== STREAMLIT UI ====================

# Page config
st.set_page_config(
    page_title="RecruitIQ - AI Talent Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

logger.info("Streamlit page configured")

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 3rem;
    border-radius: 15px;
    color: white;
    margin-bottom: 2rem;
    text-align: center;
}
.recruit-iq {
    font-size: 4rem;
    font-weight: 900;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}
.recruit {
    color: #FFD700;
}
.iq {
    color: #FFFFFF;
}
.nav-card {
    background: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    cursor: pointer;
    transition: transform 0.3s, box-shadow 0.3s;
    border: 3px solid transparent;
    min-height: 200px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.nav-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    border-color: #667eea;
}
.nav-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}
.nav-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #333;
    margin-bottom: 0.5rem;
}
.nav-desc {
    font-size: 0.9rem;
    color: #666;
}
.metric-card {
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    text-align: center;
}
.score-excellent {
    color: #10b981;
    font-size: 3rem;
    font-weight: bold;
}
.score-good {
    color: #f59e0b;
    font-size: 3rem;
    font-weight: bold;
}
.score-fair {
    color: #ef4444;
    font-size: 3rem;
    font-weight: bold;
}
.insight-positive {
    background: #d1fae5;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #10b981;
    color: #0d3b2e;              /* ADD THIS */
}
.insight-warning {
    background: #fed7aa;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #f59e0b;
}
.insight-risk {
    background: #fee2e2;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #ef4444;
    color: #5e0b0b;              /* ADD THIS */
}
/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #2c3e50;
}
[data-testid="stSidebar"] .stMarkdown {
    color: white;
}
.sidebar-nav-button {
    width: 100%;
    text-align: left;
    padding: 0.75rem 1rem;
    margin: 0.25rem 0;
    border-radius: 8px;
    background: transparent;
    color: white;
    border: none;
    cursor: pointer;
    transition: background 0.3s;
    font-size: 1rem;
}
.sidebar-nav-button:hover {
    background: rgba(255,255,255,0.1);
}
.sidebar-nav-button.active {
    background: #667eea;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'interview_questions' not in st.session_state:
    st.session_state.interview_questions = None
if 'selected_candidate' not in st.session_state:
    st.session_state.selected_candidate = None
if 'team_dynamics_result' not in st.session_state:
    st.session_state.team_dynamics_result = None

# ==================== SIDEBAR NAVIGATION ====================
with st.sidebar:
    st.markdown("### Navigate")

    # Home button
    if st.button("🏠 Home", key="sidebar_home", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'home' else "secondary"):
        st.session_state.current_page = 'home'
        logger.info("Navigation: Home")
        st.rerun()

    # CV Screening button
    if st.button("📄 CV Screening", key="sidebar_cv", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'cv_screening' else "secondary"):
        st.session_state.current_page = 'cv_screening'
        logger.info("Navigation: CV Screening")
        st.rerun()

    # Team Dynamics button
    if st.button("🔮 Team Dynamics", key="sidebar_dynamics", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'team_dynamics' else "secondary"):
        st.session_state.current_page = 'team_dynamics'
        logger.info("Navigation: Team Dynamics")
        st.rerun()

    # Interview Generator button
    if st.button("📅 Interview Generator", key="sidebar_interview", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'interview' else "secondary"):
        st.session_state.current_page = 'interview'
        logger.info("Navigation: Interview Generator")
        st.rerun()

    # Settings button
    if st.button("⚙️ Settings", key="sidebar_settings", use_container_width=True,
                 type="primary" if st.session_state.current_page == 'settings' else "secondary"):
        st.session_state.current_page = 'settings'
        logger.info("Navigation: Settings")
        st.rerun()

    st.markdown("---")

    # Quick stats in sidebar
    st.markdown("### Quick Stats")
    apps = get_all_applications()
    st.metric("Candidates", len(apps), delta=None)
    if st.session_state.analysis_result:
        score = st.session_state.analysis_result.get('matchScore', 0)
        st.metric("Last Score", f"{score}%")

# ==================== HOME PAGE ====================
if st.session_state.current_page == 'home':
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 class="recruit-iq"><span class="recruit">Recruit</span><span class="iq">IQ</span></h1>
        <p style="font-size: 1.5rem; margin-top: 1rem;">AI-Powered Talent Intelligence Platform</p>
        <p style="font-size: 1.1rem; opacity: 0.9;">Revolutionizing recruitment with advanced AI analytics & team dynamics prediction</p>
    </div>
    """, unsafe_allow_html=True)

    logger.info("User on home page")

    # Navigation Cards
    st.markdown("### 🚀 Choose Your Workflow")

    col1, col2 = st.columns(2)

    with col1:
        # CV Screening Card
        cv_clicked = st.button("📄 CV Screening", key="home_nav_cv", use_container_width=True, help="Analyze resumes")
        if cv_clicked:
            st.session_state.current_page = 'cv_screening'
            logger.info("Navigation: Home -> CV Screening")
            st.rerun()

        with st.container():
            st.markdown("""
            <div class="nav-card">
                <div class="nav-icon">📄</div>
                <div class="nav-title">CV Screening</div>
                <div class="nav-desc">Analyze resumes against job requirements with AI-powered matching</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Interview Generator Card
        interview_clicked = st.button("📅 Interview Generator", key="home_nav_interview", use_container_width=True,
                                      help="Generate questions")
        if interview_clicked:
            st.session_state.current_page = 'interview'
            logger.info("Navigation: Home -> Interview Generator")
            st.rerun()

        with st.container():
            st.markdown("""
            <div class="nav-card">
                <div class="nav-icon">📅</div>
                <div class="nav-title">Interview Generator</div>
                <div class="nav-desc">Generate personalized interview questions tailored to each candidate</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Team Dynamics Card
        dynamics_clicked = st.button("🔮 Team Dynamics", key="home_nav_dynamics", use_container_width=True,
                                     help="Predict team fit")
        if dynamics_clicked:
            st.session_state.current_page = 'team_dynamics'
            logger.info("Navigation: Home -> Team Dynamics")
            st.rerun()

        with st.container():
            st.markdown("""
            <div class="nav-card">
                <div class="nav-icon">🔮</div>
                <div class="nav-title">Team Dynamics</div>
                <div class="nav-desc">Predict team fit with personality profiling & cultural alignment</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Settings Card
        settings_clicked = st.button("⚙️ Settings & Logs", key="home_nav_settings", use_container_width=True,
                                     help="Configure system")
        if settings_clicked:
            st.session_state.current_page = 'settings'
            logger.info("Navigation: Home -> Settings")
            st.rerun()

        with st.container():
            st.markdown("""
            <div class="nav-card">
                <div class="nav-icon">⚙️</div>
                <div class="nav-title">Settings & Logs</div>
                <div class="nav-desc">Configure system settings, view logs, and manage candidates</div>
            </div>
            """, unsafe_allow_html=True)

    # Stats Section
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")

    apps = get_all_applications()
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Candidates", len(apps))
    with col2:
        analyzed = 1 if st.session_state.analysis_result else 0
        st.metric("Analyzed Today", analyzed)
    with col3:
        avg_score = st.session_state.analysis_result.get('matchScore', 0) if st.session_state.analysis_result else 0
        st.metric("Avg Match Score", f"{avg_score:.0f}%")
    with col4:
        interviewed = len(st.session_state.interview_questions) if st.session_state.interview_questions else 0
        st.metric("Interview Questions", interviewed)


# ==================== CV SCREENING PAGE ====================
elif st.session_state.current_page == 'cv_screening':
    st.markdown("""
    <div class="main-header">
        <h1 class="recruit-iq"><span class="recruit">Recruit</span><span class="iq">IQ</span></h1>
        <p style="font-size: 1.3rem;">📄 CV Screening & Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    logger.info("User on CV Screening page")

    # Candidate Selection
    st.subheader("🔍 Select Candidate from Database")

    applications = get_all_applications()

    if applications:
        candidate_options = {
            f"{app['application_id']} - {app['cv_filename']}": app['application_id']
            for app in applications
        }

        selected_option = st.selectbox(
            "Choose a candidate:",
            options=list(candidate_options.keys()),
            index=None,
            placeholder="Select a candidate to analyze..."
        )

        if selected_option:
            app_id = candidate_options[selected_option]
            logger.info(f"User selected candidate: {app_id}")
            candidate = get_application(app_id)

            if candidate:
                st.session_state.selected_candidate = candidate

                with st.expander("📋 Candidate Preview", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(f"**Application ID:** {candidate['application_id']}")
                        st.write(f"**CV File:** {candidate['cv_filename']}")
                        st.write(f"**Submitted:** {candidate['submitted_at']}")
                    with col2:
                        st.metric("Communication", candidate['communication_style'])
                        st.metric("Work Process", candidate['work_process'])

                st.markdown("---")
    else:
        st.info("📭 No candidates in database. Please submit applications first.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📤 Job Requirements")

        if st.session_state.selected_candidate:
            cv_text = st.session_state.selected_candidate['cv_text']
            st.text_area("Candidate CV (from database)", value=cv_text, height=200, disabled=True)
        else:
            cv_text = st.text_area("Candidate CV", height=200, placeholder="Select a candidate from database above...")

        job_description = st.text_area("Job Description", height=300, placeholder="Paste job description here...")

        if st.button("🔍 Analyze CV", type="primary", use_container_width=True):
            if cv_text and job_description:
                with st.spinner("Analyzing CV with AI..."):
                    try:
                        client = get_genai_client()

                        prompt = f"""Analyze this CV against the job description:

CV:
{cv_text}

Job Description:
{job_description}

Respond in JSON:
{{
  "matchScore": <0-100>,
  "skillsMatched": [list],
  "skillsGap": [list],
  "experienceRelevance": "<text>",
  "recommendation": "<Strong Fit/Good Fit/Potential Fit/Not a Fit>",
  "summary": "<2-3 sentences>",
  "strengths": [list],
  "concerns": [list]
}}"""

                        resp = client.models.generate_content(model="gemini-2.0-flash-exp", contents=prompt)
                        response_text = getattr(resp, "text", None) or str(resp)

                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            result = json.loads(response_text[json_start:json_end])
                            st.session_state.analysis_result = result
                            logger.info(f"CV analysis successful - Match score: {result.get('matchScore', 0)}")
                            st.success("✅ Analysis complete!")
                        else:
                            st.error("Failed to parse AI response")
                    except Exception as e:
                        logger.error(f"CV analysis error: {str(e)}", exc_info=True)
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please select a candidate and provide job description")

    with col2:
        st.subheader("📊 Analysis Results")

        if st.session_state.analysis_result:
            result = st.session_state.analysis_result

            score = result.get('matchScore', 0)
            score_class = "score-excellent" if score >= 80 else "score-good" if score >= 60 else "score-fair"

            st.markdown(f"""
<div class="metric-card">
<p style="color: #666; margin-bottom: 0.5rem;">Match Score</p>
<div class="{score_class}">{score}%</div>
<p style="color: #666; margin-top: 0.5rem;">{result.get('recommendation', 'N/A')}</p>
</div>
""", unsafe_allow_html=True)

            st.markdown("---")

            if result.get('skillsMatched'):
                st.markdown("**✅ Skills Matched**")
                cols = st.columns(3)
                for idx, skill in enumerate(result['skillsMatched']):
                    with cols[idx % 3]:
                        st.markdown(f"🟢 {skill}")

            st.markdown("---")

            if result.get('skillsGap'):
                st.markdown("**⚠️ Skills Gap**")
                cols = st.columns(3)
                for idx, skill in enumerate(result['skillsGap']):
                    with cols[idx % 3]:
                        st.markdown(f"🟡 {skill}")

            st.markdown("---")

            if result.get('summary'):
                st.info(f"**Summary:** {result['summary']}")

            if result.get('strengths'):
                with st.expander("💪 Strengths"):
                    for strength in result['strengths']:
                        st.write(f"• {strength}")

            if result.get('concerns'):
                with st.expander("⚠️ Concerns"):
                    for concern in result['concerns']:
                        st.write(f"• {concern}")

            # Email Actions
            st.markdown("---")
            st.subheader("📧 Send Decision Email")

            if st.session_state.selected_candidate:
                cand = st.session_state.selected_candidate
                candidate_email = st.text_input("Candidate Email", placeholder="candidate@example.com", key="email_cv")
                position = st.text_input("Position Title", placeholder="Software Engineer", key="position_cv")

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("✅ Send Shortlist Email", type="primary", use_container_width=True):
                        if candidate_email and position:
                            interview_date = st.text_input("Interview Date (Optional)",
                                                           placeholder="e.g., Next Monday, 10 AM")
                            success = send_shortlist_email(
                                cand.get('cv_filename', 'Candidate'),
                                candidate_email,
                                position,
                                interview_date if interview_date else None
                            )
                            if success:
                                st.success("✅ Shortlist email sent successfully!")
                                logger.info(f"Shortlist email sent to {candidate_email}")
                        else:
                            st.warning("Please enter email and position")

                with col_b:
                    if st.button("❌ Send Rejection Email", use_container_width=True):
                        if candidate_email and position:
                            success = send_rejection_email(
                                cand.get('cv_filename', 'Candidate'),
                                candidate_email,
                                position
                            )
                            if success:
                                st.success("✅ Rejection email sent successfully!")
                                logger.info(f"Rejection email sent to {candidate_email}")
                        else:
                            st.warning("Please enter email and position")
        else:
            st.info("👈 Select candidate and analyze to see results")


# ==================== TEAM DYNAMICS PAGE ====================
elif st.session_state.current_page == 'team_dynamics':
    st.markdown("""
    <div class="main-header">
        <h1 class="recruit-iq"><span class="recruit">Recruit</span><span class="iq">IQ</span></h1>
        <p style="font-size: 1.3rem;">🔮 Team Dynamics & Visualizations</p>
    </div>
    """, unsafe_allow_html=True)

    logger.info("User on Team Dynamics page")

    if not st.session_state.selected_candidate:
        st.warning("⚠️ Please select a candidate from CV Screening first")
        if st.button("Go to CV Screening"):
            st.session_state.current_page = 'cv_screening'
            st.rerun()
    else:
        candidate = st.session_state.selected_candidate

        st.subheader("🏢 Configure Team Profile")

        col1, col2, col3 = st.columns(3)

        with col1:
            team_communication = st.slider("Team Communication Style", 1, 5, 3, help="1=Real-time, 5=Async",
                                           key="td_comm")
            team_work_process = st.slider("Team Work Process", 1, 5, 3, help="1=Collaborative, 5=Independent",
                                          key="td_work")

        with col2:
            team_checkin_frequency = st.slider("Team Check-in Frequency", 1, 5, 3, help="1=Daily, 5=Monthly+",
                                               key="td_checkin")
            team_work_environment = st.slider("Team Work Environment", 1, 5, 3, help="1=Office, 5=Remote", key="td_env")

        with col3:
            team_schedule_structure = st.slider("Team Schedule Structure", 1, 5, 3, help="1=Structured, 5=Flexible",
                                                key="td_schedule")

        team_profile = {
            'team_communication': team_communication,
            'team_work_process': team_work_process,
            'team_checkin_frequency': team_checkin_frequency,
            'team_work_environment': team_work_environment,
            'team_schedule_structure': team_schedule_structure
        }

        if st.button("🔬 Analyze Team Dynamics", type="primary", use_container_width=True):
            with st.spinner("🔄 Running team dynamics analysis..."):
                try:
                    state = {
                        'cv_text': candidate['cv_text'],
                        'candidate_profile': {
                            'communication_style': candidate['communication_style'],
                            'work_process': candidate['work_process'],
                            'checkin_frequency': candidate['checkin_frequency'],
                            'work_environment': candidate['work_environment'],
                            'schedule_structure': candidate['schedule_structure']
                        },
                        'team_profile': team_profile,
                        'parsed_cv': {'name': candidate.get('cv_filename', 'Unknown')},
                        'errors': []
                    }

                    result_state = team_dynamics_prediction_node(state)

                    # Calculate culture fit
                    async_score = 100 - abs(candidate['communication_style'] - team_communication) * 20
                    structure_score = 100 - abs(candidate['work_process'] - team_work_process) * 20
                    checkin_score = 100 - abs(candidate['checkin_frequency'] - team_checkin_frequency) * 20
                    environment_score = 100 - abs(candidate['work_environment'] - team_work_environment) * 20
                    schedule_score = 100 - abs(candidate['schedule_structure'] - team_schedule_structure) * 20

                    culture_fit_score = (
                            0.25 * max(0, min(100, async_score)) +
                            0.25 * max(0, min(100, structure_score)) +
                            0.20 * max(0, min(100, checkin_score)) +
                            0.20 * max(0, min(100, environment_score)) +
                            0.10 * max(0, min(100, schedule_score))
                    )

                    st.session_state.team_dynamics_result = {
                        'personality_profile': result_state.get('personality_profile', {}),
                        'team_synergy_score': result_state.get('team_synergy_score', 0),
                        'conflict_risk_areas': result_state.get('conflict_risk_areas', []),
                        'collaboration_strengths': result_state.get('collaboration_strengths', []),
                        'culture_fit_score': round(culture_fit_score, 1),
                        'subscores': {
                            'async': round(max(0, min(100, async_score)), 1),
                            'structure': round(max(0, min(100, structure_score)), 1),
                            'checkin': round(max(0, min(100, checkin_score)), 1),
                            'environment': round(max(0, min(100, environment_score)), 1),
                            'schedule': round(max(0, min(100, schedule_score)), 1)
                        },
                        'candidate_values': [
                            candidate['communication_style'],
                            candidate['work_process'],
                            candidate['checkin_frequency'],
                            candidate['work_environment'],
                            candidate['schedule_structure']
                        ],
                        'team_values': [
                            team_communication,
                            team_work_process,
                            team_checkin_frequency,
                            team_work_environment,
                            team_schedule_structure
                        ]
                    }

                    logger.info("Team dynamics analysis completed successfully")
                    st.success("✅ Team dynamics analysis complete!")
                    st.balloons()

                except Exception as e:
                    logger.error(f"Team dynamics analysis error: {str(e)}", exc_info=True)
                    st.error(f"Error: {str(e)}")

        st.markdown("---")

        # Display Results
        if st.session_state.team_dynamics_result:
            result = st.session_state.team_dynamics_result

            st.subheader("📊 Key Metrics")
            col1, col2, col3 = st.columns(3)

            with col1:
                culture_score = result['culture_fit_score']
                st.metric("Culture Fit Score", f"{culture_score:.0f}%",
                          delta="Excellent" if culture_score >= 80 else "Good" if culture_score >= 60 else "Fair")

            with col2:
                synergy_score = result['team_synergy_score']
                st.metric("Team Synergy Score", f"{synergy_score:.0f}%",
                          delta="Strong" if synergy_score >= 80 else "Moderate" if synergy_score >= 60 else "Weak")

            with col3:
                risk_count = len(result['conflict_risk_areas'])
                st.metric("Conflict Risk Areas", risk_count,
                          delta="Low" if risk_count <= 1 else "Medium" if risk_count <= 3 else "High",
                          delta_color="inverse")

            st.markdown("---")

            # Personality Profile
            st.subheader("👤 Personality Profile")
            personality = result.get('personality_profile', {})

            if personality:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Work Characteristics**")
                    st.info(f"🎯 **Work Style:** {personality.get('workStyle', 'N/A').title()}")
                    st.info(f"💬 **Communication:** {personality.get('communicationStyle', 'N/A').title()}")
                    st.info(f"⚡ **Decision Making:** {personality.get('decisionMaking', 'N/A').title()}")

                with col2:
                    st.markdown("**Performance Indicators**")
                    st.info(f"💪 **Stress Response:** {personality.get('stressResponse', 'N/A').title()}")
                    st.info(f"👑 **Leadership Potential:** {personality.get('leadershipPotential', 'N/A').title()}")

            st.markdown("---")

            # Team Synergy Gauge
            st.subheader("🤝 Team Synergy Analysis")

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=result['team_synergy_score'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Team Synergy Score"},
                delta={'reference': 75},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 75], 'color': "lightyellow"},
                        {'range': [75, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 85
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("---")

            # Strengths and Risks
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ Collaboration Strengths")
                strengths = result.get('collaboration_strengths', [])
                if strengths:
                    for strength in strengths:
                        st.markdown(f'<div class="insight-positive">• {strength}</div>', unsafe_allow_html=True)
                else:
                    st.info("No specific strengths identified")

            with col2:
                st.subheader("⚠️ Conflict Risk Areas")
                risks = result.get('conflict_risk_areas', [])
                if risks:
                    for risk in risks:
                        st.markdown(f'<div class="insight-risk">• {risk}</div>', unsafe_allow_html=True)
                else:
                    st.success("No significant conflict risks identified")

            st.markdown("---")

            # Visualizations
            st.subheader("📈 Visual Analytics")

            st.markdown("#### 🕸️ Candidate vs Team Profile Match")

            categories = ['Communication', 'Work Process', 'Check-ins', 'Environment', 'Schedule']

            fig_radar = go.Figure()

            fig_radar.add_trace(go.Scatterpolar(
                r=result['candidate_values'],
                theta=categories,
                fill='toself',
                name='Candidate',
                line_color='#667eea',
                fillcolor='rgba(102, 126, 234, 0.3)'
            ))

            fig_radar.add_trace(go.Scatterpolar(
                r=result['team_values'],
                theta=categories,
                fill='toself',
                name='Team',
                line_color='#f59e0b',
                fillcolor='rgba(245, 158, 11, 0.3)'
            ))

            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=True,
                height=500
            )

            st.plotly_chart(fig_radar, use_container_width=True)

            st.markdown("---")

            # Culture Fit Subscores
            st.markdown("#### 📊 Culture Fit Breakdown")

            subscores = result['subscores']

            fig_subscores = go.Figure(data=[
                go.Bar(
                    x=list(subscores.values()),
                    y=list(subscores.keys()),
                    orientation='h',
                    marker=dict(
                        color=list(subscores.values()),
                        colorscale='RdYlGn',
                        cmin=0,
                        cmax=100,
                        showscale=True,
                        colorbar=dict(title="Score")
                    ),
                    text=[f"{v:.0f}%" for v in subscores.values()],
                    textposition='outside'
                )
            ])

            fig_subscores.update_layout(
                xaxis_title="Score",
                yaxis_title="",
                xaxis_range=[0, 110],
                height=350,
                showlegend=False
            )

            st.plotly_chart(fig_subscores, use_container_width=True)

            st.markdown("---")

            # Hiring Decision Matrix
            st.markdown("#### 🎯 Hiring Decision Matrix")

            if st.session_state.analysis_result:
                skill_score = st.session_state.analysis_result.get('matchScore', 0)
                team_synergy = result['team_synergy_score']

                fig_matrix = go.Figure()

                fig_matrix.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50, fillcolor="rgba(239, 68, 68, 0.2)",
                                     line_width=0)
                fig_matrix.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50, fillcolor="rgba(245, 158, 11, 0.2)",
                                     line_width=0)
                fig_matrix.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100, fillcolor="rgba(245, 158, 11, 0.2)",
                                     line_width=0)
                fig_matrix.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100, fillcolor="rgba(16, 185, 129, 0.2)",
                                     line_width=0)

                fig_matrix.add_trace(go.Scatter(
                    x=[skill_score],
                    y=[team_synergy],
                    mode='markers+text',
                    marker=dict(size=20, color='#667eea'),
                    text=['Candidate'],
                    textposition='top center',
                    name='Candidate Position'
                ))

                fig_matrix.add_annotation(x=25, y=25, text="Skill & Culture Gap<br>❌ No Hire", showarrow=False,
                                          font=dict(size=10))
                fig_matrix.add_annotation(x=75, y=25, text="Skills Strong<br>Culture Risk<br>⚠️ Maybe", showarrow=False,
                                          font=dict(size=10))
                fig_matrix.add_annotation(x=25, y=75, text="Culture Fit<br>Skills Gap<br>⚠️ Train", showarrow=False,
                                          font=dict(size=10))
                fig_matrix.add_annotation(x=75, y=75, text="Strong Match<br>✅ Hire", showarrow=False,
                                          font=dict(size=10))

                fig_matrix.update_layout(
                    xaxis_title="Skill Match Score",
                    yaxis_title="Team Synergy Score",
                    xaxis_range=[0, 100],
                    yaxis_range=[0, 100],
                    height=500,
                    showlegend=False
                )

                st.plotly_chart(fig_matrix, use_container_width=True)
            else:
                st.info("Complete CV analysis to see the hiring decision matrix")
        else:
            st.info("👆 Configure team profile and click 'Analyze Team Dynamics' to see results")


# ==================== INTERVIEW PAGE ====================
elif st.session_state.current_page == 'interview':
    st.markdown("""
    <div class="main-header">
        <h1 class="recruit-iq"><span class="recruit">Recruit</span><span class="iq">IQ</span></h1>
        <p style="font-size: 1.3rem;">📅 Interview Question Generator</p>
    </div>
    """, unsafe_allow_html=True)

    logger.info("User on Interview Generator page")

    if st.button("🎯 Generate Personalized Interview Questions", type="primary"):
        if not st.session_state.selected_candidate:
            st.warning("⚠️ Please select a candidate from CV Screening first")
            if st.button("Go to CV Screening"):
                st.session_state.current_page = 'cv_screening'
                st.rerun()
        elif st.session_state.analysis_result:
            with st.spinner("Generating interview questions..."):
                try:
                    client = get_genai_client()
                    candidate = st.session_state.selected_candidate
                    cv_text = candidate['cv_text']

                    team_dynamics_info = ""
                    if st.session_state.team_dynamics_result:
                        td = st.session_state.team_dynamics_result
                        team_dynamics_info = f"""
Team Dynamics Analysis:
- Team Synergy Score: {td['team_synergy_score']:.0f}%
- Personality: {json.dumps(td.get('personality_profile', {}), indent=2)}
- Conflict Risks: {', '.join(td.get('conflict_risk_areas', []))}
"""

                    prompt = f"""Generate 10 personalized interview questions:

Candidate CV:
{cv_text}

Candidate Culture Profile:
- Communication Style: {candidate['communication_style']}/5
- Work Process: {candidate['work_process']}/5
- Check-in Frequency: {candidate['checkin_frequency']}/5
- Work Environment: {candidate['work_environment']}/5
- Schedule Structure: {candidate['schedule_structure']}/5

CV Analysis:
{json.dumps(st.session_state.analysis_result, indent=2)}

{team_dynamics_info}

Create:
- Technical (3-4 questions)
- Behavioral (2-3 questions)
- Situational (2-3 questions)
- Team dynamics (1-2 questions)

JSON format:
{{
  "questions": [
    {{
      "question": "<text>",
      "category": "<Technical/Behavioral/Situational/Team Dynamics>",
      "purpose": "<why>",
      "follow_up": "<optional>"
    }}
  ]
}}"""

                    resp = client.models.generate_content(model="gemini-2.0-flash-exp", contents=prompt)
                    response_text = getattr(resp, "text", None) or str(resp)

                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        result = json.loads(response_text[json_start:json_end])
                        st.session_state.interview_questions = result['questions']
                        logger.info(f"Generated {len(result['questions'])} interview questions")
                        st.success("✅ Interview questions generated!")
                    else:
                        st.error("Failed to parse AI response")
                except Exception as e:
                    logger.error(f"Interview generation error: {str(e)}", exc_info=True)
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("⚠️ Please complete CV analysis first")

    if st.session_state.interview_questions:
        st.markdown("---")

        questions = st.session_state.interview_questions

        categories = {}
        for q in questions:
            cat = q.get('category', 'General')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(q)

        for category, cat_questions in categories.items():
            st.subheader(f"📌 {category} Questions")

            for idx, q in enumerate(cat_questions, 1):
                with st.expander(f"**Q{idx}**: {q['question'][:80]}..." if len(q['question']) > 80
                                 else f"**Q{idx}**: {q['question']}", expanded=idx == 1):
                    st.markdown(f"**Question:** {q['question']}")
                    st.markdown(f"**Purpose:** {q['purpose']}")
                    if q.get('follow_up'):
                        st.markdown(f"**Follow-up:** {q['follow_up']}")

                    st.markdown("---")
                    st.text_area(f"Interviewer Notes (Q{idx})",
                                 placeholder="Add your notes here...",
                                 key=f"notes_{category}_{idx}",
                                 height=100)

            st.markdown("---")

        # Export
        st.subheader("📥 Export Interview Guide")

        col1, col2 = st.columns(2)

        with col1:
            interview_json = json.dumps(questions, indent=2)
            st.download_button(
                label="Download as JSON",
                data=interview_json,
                file_name=f"interview_questions_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )

        with col2:
            interview_text = f"""INTERVIEW GUIDE
{'=' * 50}
Candidate: {st.session_state.selected_candidate.get('application_id', 'Unknown')}
Date: {datetime.now().strftime('%Y-%m-%d')}
CV Analysis Score: {st.session_state.analysis_result.get('matchScore', 'N/A')}

"""
            for category, cat_questions in categories.items():
                interview_text += f"\n{category.upper()} QUESTIONS\n{'-' * 50}\n"
                for idx, q in enumerate(cat_questions, 1):
                    interview_text += f"\nQ{idx}: {q['question']}\n"
                    interview_text += f"Purpose: {q['purpose']}\n"
                    if q.get('follow_up'):
                        interview_text += f"Follow-up: {q['follow_up']}\n"
                    interview_text += "\nNotes:\n_____________________\n\n"

            st.download_button(
                label="Download as Text",
                data=interview_text,
                file_name=f"interview_guide_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )


# ==================== SETTINGS PAGE ====================
elif st.session_state.current_page == 'settings':
    st.markdown("""
    <div class="main-header">
        <h1 class="recruit-iq"><span class="recruit">Recruit</span><span class="iq">IQ</span></h1>
        <p style="font-size: 1.3rem;">⚙️ Settings & System Logs</p>
    </div>
    """, unsafe_allow_html=True)

    logger.info("User on Settings page")

    st.subheader("💾 Database Configuration")
    st.info(f"**Current Database:** {DATABASE_PATH}")

    apps = get_all_applications()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Candidates", len(apps))
    with col2:
        analyzed = 1 if st.session_state.analysis_result else 0
        st.metric("Analyzed Today", analyzed)
    with col3:
        avg_score = st.session_state.analysis_result.get('matchScore', 0) if st.session_state.analysis_result else 0
        st.metric("Avg Score", f"{avg_score:.0f}")

    st.markdown("---")

    st.subheader("📊 Culture Fit Weights")
    st.info("Default weights for culture fit calculation")

    col1, col2 = st.columns(2)
    with col1:
        communication_weight = st.slider("Communication Weight", 0, 100, 25)
        work_process_weight = st.slider("Work Process Weight", 0, 100, 25)
        checkin_weight = st.slider("Check-in Frequency Weight", 0, 100, 20)
    with col2:
        environment_weight = st.slider("Work Environment Weight", 0, 100, 20)
        schedule_weight = st.slider("Schedule Structure Weight", 0, 100, 10)

    total_weight = communication_weight + work_process_weight + checkin_weight + environment_weight + schedule_weight
    if total_weight != 100:
        st.warning(f"⚠️ Total weight is {total_weight}%. Should be 100%")
    else:
        st.success("✅ Weights are balanced")

    st.markdown("---")

    st.subheader("🗑️ Clear Data")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Clear CV Analysis", use_container_width=True):
            st.session_state.analysis_result = None
            logger.info("CV analysis cleared")
            st.success("Cleared!")

    with col2:
        if st.button("Clear Team Dynamics", use_container_width=True):
            st.session_state.team_dynamics_result = None
            logger.info("Team dynamics cleared")
            st.success("Cleared!")

    with col3:
        if st.button("Clear Interview Questions", use_container_width=True):
            st.session_state.interview_questions = None
            logger.info("Interview questions cleared")
            st.success("Cleared!")

    st.markdown("---")

    st.subheader("📋 System Logs")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.info(f"**Log File Location:** app.log")
        st.caption("All system activities are logged with timestamps and detailed information")

    with col2:
        if st.button("View Logs", use_container_width=True):
            try:
                with open('app.log', 'r') as f:
                    log_content = f.read()
                st.text_area("Recent Logs (Last 5000 chars)", log_content[-5000:], height=400)
                logger.info("User viewed system logs")
            except FileNotFoundError:
                st.warning("Log file not found yet")

    st.markdown("---")

    st.subheader("📊 System Information")

    with st.expander("View Current Session State"):
        session_data = {
            'selected_candidate': st.session_state.selected_candidate.get(
                'application_id') if st.session_state.selected_candidate else None,
            'analysis_completed': bool(st.session_state.analysis_result),
            'team_dynamics_completed': bool(st.session_state.team_dynamics_result),
            'interview_questions_generated': bool(st.session_state.interview_questions)
        }
        st.json(session_data)

    with st.expander("View Database Schema"):
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

    with st.expander("Email Configuration"):
        st.markdown("""
        **SMTP Email Settings**

        Configured in `.env` file:
        - `SENDER_EMAIL`: Your Gmail address
        - `SENDER_PASSWORD`: Your Gmail App Password

        **Note:** Use Gmail App Passwords, not your regular password.
        [How to create App Password](https://support.google.com/accounts/answer/185833)

        Current Status:
        """)
        if SENDER_EMAIL and SENDER_PASSWORD:
            st.success(f"✅ Email configured: {SENDER_EMAIL}")
        else:
            st.error("❌ Email credentials not configured")
            st.info("Add SENDER_EMAIL and SENDER_PASSWORD to your .env file")

    with st.expander("API Documentation"):
        st.markdown("""
        **Google Gemini API**
        - Model: gemini-2.0-flash-exp
        - Temperature: 0.7 (standard)
        - Max tokens: 2000

        **Features:**
        - CV parsing and analysis
        - Skill matching against job description
        - Team dynamics prediction
        - Personality profiling
        - Culture fit calculation
        - Personalized interview questions
        - Automated email notifications

        **Logging:**
        - All API calls logged with timestamps
        - Request/response sizes tracked
        - Errors logged with full stack traces
        - Email delivery status tracked
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
<p style="font-size: 1.2rem;"><span style="color: #FFD700; font-weight: 900;">Recruit</span><span style="color: #667eea; font-weight: 900;">IQ</span> <strong>v2.0</strong> | Powered by Google Gemini</p>
<p style="font-size: 0.9rem;">✨ Features: CV Screening | Team Dynamics | Interview Generation | Email Notifications</p>
<p style="font-size: 0.8rem;">🔒 All activities logged to app.log for audit and debugging</p>
</div>
""", unsafe_allow_html=True)

logger.info("Application UI rendered successfully")