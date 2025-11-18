import streamlit as st
import json
from datetime import datetime
from dotenv import load_dotenv
import os
import sqlite3
from contextlib import contextmanager

load_dotenv()

# Import Google GenAI SDK
from google import genai

# Database configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", "applications.db")


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_all_applications():
    """Retrieve all applications from database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications ORDER BY submitted_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        st.error(f"Error retrieving applications: {e}")
        return []


def get_application(application_id: str):
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


# Page config
st.set_page_config(
    page_title="AI Talent Intelligence Platform",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
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
    }
    .insight-warning {
        background: #fed7aa;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #f59e0b;
    }
    .candidate-card {
        background: #f9fafb;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    .candidate-card:hover {
        border-color: #667eea;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'interview_questions' not in st.session_state:
    st.session_state.interview_questions = None
if 'culture_fit_result' not in st.session_state:
    st.session_state.culture_fit_result = None
if 'selected_candidate' not in st.session_state:
    st.session_state.selected_candidate = None

# Header
st.markdown("""
<div class="main-header">
    <h1>🧠 AI Talent Intelligence Platform</h1>
    <p>Advanced recruitment automation with multi-agent AI analysis</p>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📄 CV Screening", "👥 Culture Fit Assessment", "📅 Interview Generator", "⚙️ Settings"])


def get_genai_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "❌ GOOGLE_API_KEY not found! "
            "Set it in your .env file or in your Streamlit Settings tab."
        )
    return genai.Client(api_key=api_key)


# ==================== TAB 1: CV SCREENING ====================
with tab1:
    st.header("CV Screening & Analysis")

    # Candidate Selection Section
    st.subheader("🔍 Select Candidate from Database")

    applications = get_all_applications()

    if applications:
        # Create dropdown with candidate options
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
            candidate = get_application(app_id)

            if candidate:
                st.session_state.selected_candidate = candidate

                # Display candidate preview
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

        # Show CV from database if candidate is selected
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

                        prompt = f"""Analyze this CV against the job description and provide a detailed assessment.

CV:
{cv_text}

Job Description:
{job_description}

Respond in JSON format with the following structure:
{{
    "matchScore": <number 0-100>,
    "skillsMatched": [<list of matched skills>],
    "skillsGap": [<list of missing skills>],
    "experienceRelevance": "<brief assessment>",
    "recommendation": "<Strong Fit/Good Fit/Potential Fit/Not a Fit>",
    "summary": "<2-3 sentence summary>",
    "strengths": [<list of candidate strengths>],
    "concerns": [<list of concerns>]
}}"""

                        resp = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=prompt
                        )

                        response_text = getattr(resp, "text", None) or str(resp)

                        json_start = response_text.find('{')
                        json_end = response_text.rfind('}') + 1
                        if json_start != -1 and json_end > json_start:
                            result = json.loads(response_text[json_start:json_end])
                            st.session_state.analysis_result = result
                            st.success("✅ Analysis complete!")
                        else:
                            st.error("Failed to parse AI response")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please select a candidate and provide job description")

    with col2:
        st.subheader("📊 Analysis Results")

        if st.session_state.analysis_result:
            result = st.session_state.analysis_result

            # Match Score
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

            # Skills Matched
            if result.get('skillsMatched'):
                st.markdown("**✅ Skills Matched**")
                cols = st.columns(3)
                for idx, skill in enumerate(result['skillsMatched']):
                    with cols[idx % 3]:
                        st.markdown(f"🟢 {skill}")

            st.markdown("---")

            # Skills Gap
            if result.get('skillsGap'):
                st.markdown("**⚠️ Skills Gap**")
                cols = st.columns(3)
                for idx, skill in enumerate(result['skillsGap']):
                    with cols[idx % 3]:
                        st.markdown(f"🟡 {skill}")

            st.markdown("---")

            # Summary
            if result.get('summary'):
                st.info(f"**Summary:** {result['summary']}")

            # Strengths
            if result.get('strengths'):
                with st.expander("💪 Strengths"):
                    for strength in result['strengths']:
                        st.write(f"• {strength}")

            # Concerns
            if result.get('concerns'):
                with st.expander("⚠️ Concerns"):
                    for concern in result['concerns']:
                        st.write(f"• {concern}")
        else:
            st.info("👈 Select candidate and analyze to see results")

# ==================== TAB 2: CULTURE FIT ====================
with tab2:
    st.header("Culture Fit Assessment")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👤 Candidate Profile (from Database)")

        if st.session_state.selected_candidate:
            candidate = st.session_state.selected_candidate

            # Display candidate culture answers from database
            st.info(f"**Candidate:** {candidate['application_id']}")

            async_comfort = candidate['communication_style']
            st.metric("Async Communication Comfort", f"{async_comfort}/5",
                      help="1 = Need sync communication, 5 = Love async")

            process_preference = candidate['work_process']
            st.metric("Process Preference", f"{process_preference}/5",
                      help="1 = Prefer flexible workflows, 5 = Prefer structured processes")

            meeting_frequency = candidate['checkin_frequency']
            st.metric("Meeting Frequency Preference", f"{meeting_frequency}/5",
                      help="1 = Minimal meetings, 5 = Frequent check-ins")

            remote_preference = candidate['work_environment']
            st.metric("Remote Work Preference", f"{remote_preference}/5",
                      help="1 = Prefer office, 5 = Prefer remote")

            # Also show schedule structure
            schedule_structure = candidate['schedule_structure']
            st.metric("Schedule Structure", f"{schedule_structure}/5",
                      help="1 = Highly structured, 5 = Highly flexible")
        else:
            st.warning("👈 Please select a candidate from Tab 1 first")
            async_comfort = 3
            process_preference = 3
            meeting_frequency = 3
            remote_preference = 3

        st.markdown("---")

        st.subheader("🏢 Team Profile")

        team_communication = st.slider(
            "Team Communication Style",
            min_value=1, max_value=5, value=3,
            help="1 = Prefer real-time meetings, 5 = Prefer async communication"
        )

        team_work_process = st.slider(
            "Team Work Process",
            min_value=1, max_value=5, value=3,
            help="1 = Highly collaborative, 5 = Highly independent"
        )

        team_checkin_frequency = st.slider(
            "Team Check-in Frequency",
            min_value=1, max_value=5, value=3,
            help="1 = Daily meetings, 5 = Monthly or less"
        )

        team_work_environment = st.slider(
            "Team Work Environment",
            min_value=1, max_value=5, value=3,
            help="1 = Office only, 5 = Remote only"
        )

        team_schedule_structure = st.slider(
            "Team Schedule Structure",
            min_value=1, max_value=5, value=3,
            help="1 = Highly structured, 5 = Highly flexible"
        )

        if st.button("🧮 Calculate Culture Fit", type="primary", use_container_width=True):
            if not st.session_state.selected_candidate:
                st.warning("⚠️ Please select a candidate from Tab 1 first")
            else:
                # Calculate subscores - lower difference = better match
                communication_score = max(0, min(100, 100 - abs(async_comfort - team_communication) * 20))
                work_process_score = max(0, min(100, 100 - abs(process_preference - team_work_process) * 20))
                checkin_score = max(0, min(100, 100 - abs(meeting_frequency - team_checkin_frequency) * 20))
                environment_score = max(0, min(100, 100 - abs(remote_preference - team_work_environment) * 20))
                schedule_score = max(0, min(100, 100 - abs(schedule_structure - team_schedule_structure) * 20))

                # Total weighted score
                total_score = (
                        0.25 * communication_score +
                        0.25 * work_process_score +
                        0.20 * checkin_score +
                        0.20 * environment_score +
                        0.10 * schedule_score
                )

                # Generate insights
                insights = []
                if communication_score >= 80:
                    insights.append(("positive", "Excellent communication style alignment"))
                elif communication_score < 60:
                    insights.append(("warning", "Communication style mismatch - discuss expectations"))

                if work_process_score >= 80:
                    insights.append(("positive", "Strong work process compatibility"))
                elif work_process_score < 60:
                    insights.append(("warning", "Work process preferences differ - may need adjustment period"))

                if checkin_score >= 80:
                    insights.append(("positive", "Great alignment on meeting frequency"))
                elif checkin_score < 60:
                    insights.append(("warning", "Check-in frequency mismatch - set clear expectations"))

                if environment_score >= 80:
                    insights.append(("positive", "Perfect work environment fit"))
                elif environment_score < 60:
                    insights.append(("warning", "Work environment preference gap - consider hybrid options"))

                if schedule_score >= 80:
                    insights.append(("positive", "Schedule structure alignment is strong"))
                elif schedule_score < 60:
                    insights.append(("warning", "Different schedule preferences - discuss flexibility needs"))

                st.session_state.culture_fit_result = {
                    "total_score": round(total_score, 1),
                    "subscores": {
                        "communication": round(communication_score, 1),
                        "work_process": round(work_process_score, 1),
                        "checkin": round(checkin_score, 1),
                        "environment": round(environment_score, 1),
                        "schedule": round(schedule_score, 1)
                    },
                    "insights": insights
                }

                st.success("✅ Culture fit calculated!")

    with col2:
        st.subheader("📊 Culture Fit Results")

        if st.session_state.culture_fit_result:
            result = st.session_state.culture_fit_result

            # Total Score
            total = result['total_score']
            score_class = "score-excellent" if total >= 80 else "score-good" if total >= 60 else "score-fair"
            fit_label = "Excellent Match" if total >= 80 else "Good Match" if total >= 60 else "Fair Match"

            st.markdown(f"""
            <div class="metric-card">
                <p style="color: #666; margin-bottom: 0.5rem;">Overall Culture Fit</p>
                <div class="{score_class}">{total}</div>
                <p style="color: #666; margin-top: 0.5rem;">{fit_label}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("---")

            # Subscores
            st.markdown("**📈 Detailed Scores**")

            col_a, col_b = st.columns(2)

            with col_a:
                st.metric("Communication Style", f"{result['subscores']['communication']}%")
                st.metric("Check-in Frequency", f"{result['subscores']['checkin']}%")
                st.metric("Schedule Structure", f"{result['subscores']['schedule']}%")

            with col_b:
                st.metric("Work Process", f"{result['subscores']['work_process']}%")
                st.metric("Work Environment", f"{result['subscores']['environment']}%")

            st.markdown("---")

            # Insights
            st.markdown("**💡 Key Insights**")
            for insight_type, insight_text in result['insights']:
                if insight_type == "positive":
                    st.markdown(f'<div class="insight-positive">✅ {insight_text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="insight-warning">⚠️ {insight_text}</div>', unsafe_allow_html=True)
        else:
            st.info("👈 Select candidate and calculate to see results")

# ==================== TAB 3: INTERVIEW GENERATOR ====================
with tab3:
    st.header("Interview Question Generator")

    if st.button("🎯 Generate Personalized Interview Questions", type="primary"):
        if not st.session_state.selected_candidate:
            st.warning("⚠️ Please select a candidate from Tab 1 first")
        elif st.session_state.analysis_result:
            with st.spinner("Generating interview questions..."):
                try:
                    client = get_genai_client()
                    candidate = st.session_state.selected_candidate
                    cv_text = candidate['cv_text']

                    prompt = f"""Generate 8-10 personalized interview questions based on this candidate profile and their culture fit.

Candidate CV:
{cv_text}

Candidate Culture Profile:
- Communication Style: {candidate['communication_style']}/5
- Work Process: {candidate['work_process']}/5
- Check-in Frequency: {candidate['checkin_frequency']}/5
- Work Environment: {candidate['work_environment']}/5
- Schedule Structure: {candidate['schedule_structure']}/5

Previous Analysis:
{json.dumps(st.session_state.analysis_result, indent=2)}

Create a mix of:
- Technical skill questions (3-4 questions)
- Behavioral questions (2-3 questions)
- Situational questions (2-3 questions)
- Culture fit questions (1-2 questions)

Respond in JSON format:
{{
    "questions": [
        {{
            "question": "<the question>",
            "category": "<Technical/Behavioral/Situational/Culture>",
            "purpose": "<why this question matters>",
            "follow_up": "<optional follow-up question>"
        }}
    ]
}}"""

                    resp = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )

                    response_text = getattr(resp, "text", None) or str(resp)
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        result = json.loads(response_text[json_start:json_end])
                        st.session_state.interview_questions = result['questions']
                        st.success("✅ Interview questions generated!")
                    else:
                        st.error("Failed to parse AI response")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("⚠️ Please complete CV analysis first (Tab 1)")

    if st.session_state.interview_questions:
        st.markdown("---")

        for idx, q in enumerate(st.session_state.interview_questions, 1):
            with st.expander(f"**Q{idx}**: {q['question'][:80]}..." if len(
                    q['question']) > 80 else f"**Q{idx}**: {q['question']}", expanded=idx <= 3):
                st.markdown(f"**Category:** `{q['category']}`")
                st.markdown(f"**Question:** {q['question']}")
                st.markdown(f"**Purpose:** {q['purpose']}")
                if q.get('follow_up'):
                    st.markdown(f"**Follow-up:** {q['follow_up']}")

# ==================== TAB 4: SETTINGS ====================
with tab4:
    st.header("⚙️ Configuration & Settings")

    st.subheader("🔑 API Configuration")
    api_key = st.text_input(
        "Google API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Enter your Google GenAI (Gemini) API key for AI-powered analysis"
    )

    if st.button("Save API Key"):
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API key saved!")

    st.markdown("---")

    st.subheader("💾 Database Configuration")
    st.info(f"**Current Database:** {DATABASE_PATH}")

    # Database stats
    apps = get_all_applications()
    st.metric("Total Candidates", len(apps))

    st.markdown("---")

    st.subheader("📊 Culture Fit Weights")
    st.info("Adjust the importance of each factor in culture fit calculation")

    col1, col2 = st.columns(2)
    with col1:
        communication_weight = st.slider("Communication Style Weight", 0, 100, 25)
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
            st.success("Cleared!")
    with col2:
        if st.button("Clear Culture Fit", use_container_width=True):
            st.session_state.culture_fit_result = None
            st.success("Cleared!")
    with col3:
        if st.button("Clear Interview Questions", use_container_width=True):
            st.session_state.interview_questions = None
            st.success("Cleared!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p>🧠 AI Talent Intelligence Platform | Powered by Gemini (Google GenAI) & Streamlit</p>
    <p style="font-size: 0.8rem;">Multi-agent recruitment automation system with database integration</p>
</div>
""", unsafe_allow_html=True)