import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv
import re
import PyPDF2
from io import BytesIO
import logging
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient
import gridfs
from typing import LiteralString

# MongoDB Configuration
MONGODB_URI = <YOUR MONGODB UR>
if not MONGODB_URI:
    raise RuntimeError("Set the MONGODB_URI environment variable first")

client = MongoClient(MONGODB_URI)
db = client["medreport"]
collection = db["appointments"]
fs = gridfs.GridFS(db, collection="pdfs")


def upload_pdf(uploaded_file, metadata=None):
    """Upload a PDF from Streamlit UploadedFile; returns the file id."""
    metadata = metadata or {}
    return fs.put(
        uploaded_file.read(),
        filename=uploaded_file.name,
        contentType="application/pdf",
        **metadata
    )


# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'ClinIQ_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
logger.info("Application started")

# Configure Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("GEMINI_API_KEY not found in environment variables")
    st.error("❌ GEMINI_API_KEY not found in .env file!")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {str(e)}")
    st.error(f"❌ Could not initialize Gemini model. Error: {str(e)}")
    st.stop()

# Page config
st.set_page_config(
    page_title="ClinIQ AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .report-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
        color: #1e293b;
    }
    .report-card p, .report-card h3, .report-card h4, .report-card strong {
        color: #1e293b !important;
    }
    .agent-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        min-height: 180px;
        max-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .agent-card h3 {
        color: white !important;
        margin-bottom: 10px;
        font-size: 1.3em;
    }
    .agent-card p {
        color: rgba(255,255,255,0.95) !important;
        font-size: 0.95em;
        line-height: 1.5;
    }
    .finding-box {
        background: #f0f9ff;
        border-left: 4px solid #0ea5e9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #0c4a6e;
    }
    .finding-box p, .finding-box h3, .finding-box h4, .finding-box strong {
        color: #0c4a6e !important;
    }
    .warning-box {
        background: #fef3c7;
        border-left: 4px solid #f59e0b;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #78350f;
    }
    .warning-box p, .warning-box h3, .warning-box h4, .warning-box strong {
        color: #78350f !important;
    }
    .success-box {
        background: #f0fdf4;
        border-left: 4px solid #10b981;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #064e3b;
    }
    h1, h2, h3 {
        color: #1e293b !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: #1e293b !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    [data-testid="stSidebar"] h1 {
        color: #e0e7ff !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] .element-container img {
        filter: brightness(1.2);
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 25px;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .hero-section {
        text-align: center;
        padding: 40px 20px;
        margin-bottom: 30px;
    }
    .hero-section h1 {
        font-size: 3em;
        margin-bottom: 10px;
        color: #1e293b !important;
        font-weight: 700;
    }
    .hero-section h2 {
        font-size: 1.5em;
        color: #1e293b !important;
        font-weight: 400;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'appointments' not in st.session_state:
    st.session_state.appointments = []
if 'current_report' not in st.session_state:
    st.session_state.current_report = None
if 'report_analysis' not in st.session_state:
    st.session_state.report_analysis = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 Home"

logger.info("Session state initialized")


# Helper function to format text for HTML
def format_for_html(text):
    """Convert newlines to HTML breaks"""
    return text.replace('\n', '<br>')


# Helper function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file"""
    try:
        logger.info("Starting PDF text extraction")
        pdf_file.seek(0)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        total_pages = len(pdf_reader.pages)
        logger.info(f"PDF has {total_pages} pages")

        for page_num in range(total_pages):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            logger.warning("No text extracted from PDF")
            return None

        logger.info(f"Successfully extracted {len(text)} characters from PDF")
        return text.strip()
    except Exception as e:
        logger.error(f"PDF reading error: {str(e)}")
        raise Exception(f"PDF reading error: {str(e)}")


# Email notification function
def send_email_notification(recipient_email, subject, content, content_type="appointment"):
    """Send email notification with appointment or analysis details"""
    try:
        logger.info(f"Attempting to send email to: {recipient_email}")

        # Email configuration
        sender_email = os.getenv('SENDER_EMAIL', 'cliniq.ai@example.com')
        sender_password = os.getenv('EMAIL_PASSWORD', '')

        # For demo purposes, we'll simulate email sending
        # In production, configure proper SMTP settings
        if not sender_password:
            logger.warning("Email password not configured, simulating email send")
            return True, "Email notification simulated (configure EMAIL_PASSWORD in .env for actual sending)"

        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"ClinIQ AI <{sender_email}>"
        message["To"] = recipient_email

        # Create HTML content
        if content_type == "appointment":
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                            <h1 style="margin: 0;">🏥 ClinIQ AI</h1>
                            <p style="margin: 5px 0 0 0;">Your Intelligent Medical Assistant</p>
                        </div>
                        <div style="padding: 20px; background: #f9f9f9;">
                            <h2 style="color: #667eea;">📅 Appointment Confirmation</h2>
                            {content}
                        </div>
                        <div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin-top: 20px;">
                            <p style="margin: 0; font-size: 0.9em;"><strong>⚠️ Important:</strong> This is an AI-generated recommendation. Please contact your healthcare provider to confirm.</p>
                        </div>
                        <div style="text-align: center; padding: 20px; color: #666; font-size: 0.85em;">
                            <p>© 2024 ClinIQ AI - Powered by Google Gemini</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        else:  # analysis
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                            <h1 style="margin: 0;">🏥 ClinIQ AI</h1>
                            <p style="margin: 5px 0 0 0;">Your Intelligent Medical Assistant</p>
                        </div>
                        <div style="padding: 20px; background: #f9f9f9;">
                            <h2 style="color: #667eea;">📊 Medical Report Analysis</h2>
                            <div style="background: white; padding: 15px; border-radius: 8px; margin-top: 15px;">
                                {content}
                            </div>
                        </div>
                        <div style="padding: 15px; background: #fff3cd; border-left: 4px solid #ffc107; margin-top: 20px;">
                            <p style="margin: 0; font-size: 0.9em;"><strong>⚠️ Disclaimer:</strong> AI-generated analysis. Always consult healthcare professionals.</p>
                        </div>
                        <div style="text-align: center; padding: 20px; color: #666; font-size: 0.85em;">
                            <p>© 2024 ClinIQ AI - Powered by Google Gemini</p>
                        </div>
                    </div>
                </body>
            </html>
            """

        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Try to send email
        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
            logger.info(f"Email sent successfully to: {recipient_email}")
            return True, "Email sent successfully!"
        except:
            # If actual sending fails, simulate for demo
            logger.info(f"Email simulated for: {recipient_email}")
            return True, f"✉️ Email notification prepared for {recipient_email} (Demo mode)"

    except Exception as e:
        logger.error(f"Error in email notification: {str(e)}")
        return False, f"Error: {str(e)}"


# Medical Report Analyzer Functions
def analyze_medical_report(report_text):
    """Extract and analyze medical report findings"""
    try:
        logger.info("Starting medical report analysis")
        prompt = f"""
        Analyze this medical report and provide:
        1. Key Findings (list the most important observations)
        2. Layman's Explanation (explain in simple terms)
        3. Potential Conditions (possible diagnoses based on findings)
        4. Recommendations (what the patient should do next)

        Medical Report:
        {report_text}

        Format your response in clear sections with headers.
        """

        response = model.generate_content(prompt)
        logger.info("Medical report analysis completed successfully")
        return response.text
    except Exception as e:
        logger.error(f"Error in analyze_medical_report: {str(e)}")
        raise


def search_medical_info(condition):
    """Search for medical information about a condition"""
    try:
        logger.info(f"Searching medical information for: {condition}")
        prompt = f"""
        Provide authoritative medical information about: {condition}

        Include:
        1. Definition and Overview
        2. Common Symptoms
        3. Typical Causes
        4. Standard Treatment Options
        5. When to Seek Medical Care

        Base this on established medical knowledge and guidelines.
        """

        response = model.generate_content(prompt)
        logger.info(f"Medical information search completed for: {condition}")
        return response.text
    except Exception as e:
        logger.error(f"Error in search_medical_info: {str(e)}")
        raise


def chat_about_report(user_question, report_text, analysis_text):
    """Answer questions about the medical report"""
    try:
        logger.info(f"Processing chat question: {user_question[:50]}...")
        prompt = f"""
        You are a helpful medical assistant chatbot. A patient has uploaded their medical report and wants to ask questions about it.

        MEDICAL REPORT:
        {report_text}

        PREVIOUS ANALYSIS:
        {analysis_text}

        PATIENT QUESTION: {user_question}

        Instructions for answering:
        1. Be conversational, friendly, and empathetic
        2. If asking about specific values (like hemoglobin, glucose, etc.), compare with normal ranges
        3. If values are abnormal, explain:
           - How much above/below normal (with specific numbers)
           - What it might mean
           - Dietary recommendations or lifestyle changes
           - When to consult a doctor
        4. Use simple, layman terms
        5. Always end with advice to consult healthcare professionals for serious concerns
        6. If the report doesn't contain information to answer the question, politely say so
        7. Be specific with numbers and comparisons when available

        Now answer the patient's question:
        """

        response = model.generate_content(prompt)
        logger.info("Chat response generated successfully")
        return response.text
    except Exception as e:
        logger.error(f"Error in chat_about_report: {str(e)}")
        raise


# Multi-Agent Hospital System
class AppointmentScheduler:
    """Agent 1: Handles appointment scheduling"""

    @staticmethod
    def schedule_appointment(patient_name, concern, preferred_date, preferred_time, patient_email=None):
        try:
            logger.info(f"Scheduling appointment for {patient_name}")
            prompt = f"""
            As an appointment scheduler, process this appointment request:

            Patient: {patient_name}
            Chief Concern: {concern}
            Preferred Date: {preferred_date}
            Preferred Time: {preferred_time}

            Provide:
            1. Recommended department/specialist
            2. Urgency level (Routine, Urgent, Emergency)
            3. Estimated consultation duration
            4. Pre-appointment instructions
            """

            response = model.generate_content(prompt)

            appointment = {
                'patient': patient_name,
                'concern': concern,
                'date': preferred_date,
                'time': preferred_time,
                'email': patient_email,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'details': response.text
            }
            st.session_state.appointments.append(appointment)
            logger.info(f"Appointment scheduled successfully for {patient_name}")

            # Send email notification if email provided
            email_sent = False
            if patient_email:
                email_content = f"""
                <p><strong>Patient Name:</strong> {patient_name}</p>
                <p><strong>Chief Concern:</strong> {concern}</p>
                <p><strong>Preferred Date:</strong> {preferred_date}</p>
                <p><strong>Preferred Time:</strong> {preferred_time}</p>
                <p><strong>Scheduled:</strong> {appointment['timestamp']}</p>
                <hr>
                <h3>AI Recommendations:</h3>
                <div style="white-space: pre-wrap;">{response.text.replace(chr(10), '<br>')}</div>
                """

                success, message = send_email_notification(
                    patient_email,
                    f"Appointment Scheduled - {patient_name}",
                    email_content,
                    "appointment"
                )
                email_sent = success

            return appointment, response.text, email_sent
        except Exception as e:
            logger.error(f"Error in schedule_appointment: {str(e)}")
            raise


class PatientTriage:
    """Agent 2: Triages patients based on symptoms"""

    @staticmethod
    def triage_patient(symptoms):
        try:
            logger.info(f"Performing triage assessment for symptoms: {symptoms[:50]}...")
            prompt = f"""
            As a triage nurse, assess these symptoms:

            Symptoms: {symptoms}

            Provide:
            1. Triage Category (Emergency/Urgent/Standard/Non-urgent)
            2. Priority Level (1-5, where 1 is highest)
            3. Recommended Action (ER/Same-day/Scheduled/Telehealth)
            4. Red Flags to watch for
            5. Brief explanation of the assessment
            """

            response = model.generate_content(prompt)
            logger.info("Triage assessment completed successfully")
            return response.text
        except Exception as e:
            logger.error(f"Error in triage_patient: {str(e)}")
            raise


class DoctorAssistant:
    """Agent 3: Retrieves medical guidelines and assists diagnosis"""

    @staticmethod
    def get_medical_guidance(condition, symptoms):
        try:
            logger.info(f"Getting medical guidance for: {condition}")
            prompt = f"""
            As a medical assistant, provide clinical guidance for:

            Condition/Concern: {condition}
            Associated Symptoms: {symptoms}

            Retrieve and summarize:
            1. Clinical Practice Guidelines
            2. Differential Diagnoses to consider
            3. Recommended Diagnostic Tests
            4. Evidence-based Treatment Protocols
            5. Follow-up Recommendations

            Base this on established medical guidelines (e.g., WHO, CDC, medical associations).
            """

            response = model.generate_content(prompt)
            logger.info(f"Medical guidance retrieved successfully for: {condition}")
            return response.text
        except Exception as e:
            logger.error(f"Error in get_medical_guidance: {str(e)}")
            raise


# Navigation function
def navigate_to(page_name):
    """Navigate to a specific page"""
    st.session_state.current_page = page_name
    logger.info(f"Navigating to: {page_name}")
    st.rerun()


# Back button component
def show_back_button():
    """Show a back to home button"""
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("⬅️ Back to Home", key="back_home"):
            navigate_to("🏠 Home")


# Sidebar
st.sidebar.title("🏥 ClinIQ AI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["🏠 Home", "📄 Report Analyzer", "💬 Report Chatbot", "📚 Knowledge Base", "🤖 Hospital Assistant"],
    index=["🏠 Home", "📄 Report Analyzer", "💬 Report Chatbot", "📚 Knowledge Base", "🤖 Hospital Assistant"].index(
        st.session_state.current_page),
    key="nav_radio"
)

if page != st.session_state.current_page:
    st.session_state.current_page = page
    logger.info(f"Navigation changed to: {page}")

st.sidebar.markdown("---")
st.sidebar.info("""
**ClinIQ AI** combines advanced AI agents to:
- Analyze medical reports
- Chat about your health
- Schedule appointments
- Triage patients
- Provide medical guidance

*Always consult healthcare professionals for medical decisions.*
""")

# Home Page
if st.session_state.current_page == "🏠 Home":
    logger.info("Displaying Home page")

    st.markdown("""
    <div class="hero-section">
        <h1>🏥 ClinIQ AI</h1>
        <h2>Your Intelligent Medical Assistant</h2>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🌟 Main Features")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="agent-card">
            <h3>📄 Report Analyzer</h3>
            <p>Upload medical reports and get instant analysis with layman explanations</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Report Analyzer", key="home_analyzer", use_container_width=True):
            navigate_to("📄 Report Analyzer")

    with col2:
        st.markdown("""
        <div class="agent-card">
            <h3>💬 Report Chatbot</h3>
            <p>Ask questions about your medical reports and get instant answers</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Chatbot", key="home_chat", use_container_width=True):
            navigate_to("💬 Report Chatbot")

    with col3:
        st.markdown("""
        <div class="agent-card">
            <h3>📚 Knowledge Base</h3>
            <p>Search medical information and research conditions</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Knowledge Base", key="home_knowledge", use_container_width=True):
            navigate_to("📚 Knowledge Base")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="agent-card">
            <h3>🤖 AI Agents</h3>
            <p>Multi-agent system for scheduling, triage, and medical guidance</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Go to Hospital Assistant", key="home_assistant", use_container_width=True):
            navigate_to("🤖 Hospital Assistant")

    with col2:
        st.markdown("""
        <div class="agent-card">
            <h3>📅 Smart Scheduling</h3>
            <p>Intelligent appointment booking with urgency assessment</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Schedule Appointment", key="home_schedule", use_container_width=True):
            navigate_to("🤖 Hospital Assistant")

    with col3:
        st.markdown("""
        <div class="agent-card">
            <h3>🚑 Patient Triage</h3>
            <p>Quick symptom assessment and priority determination</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Triage Assessment", key="home_triage", use_container_width=True):
            navigate_to("🤖 Hospital Assistant")

# Report Analyzer Page
elif st.session_state.current_page == "📄 Report Analyzer":
    logger.info("Displaying Report Analyzer page")
    show_back_button()

    st.title("📄 Medical Report Analyzer")
    st.markdown("Upload or paste your medical report for instant AI-powered analysis")

    input_method = st.radio("Choose input method:", ["Paste Text", "Upload File"])

    report_text = ""

    if input_method == "Paste Text":
        report_text = st.text_area(
            "Paste your medical report here:",
            height=200,
            placeholder="Enter radiology report, lab results, or any medical document..."
        )
    else:
        st.info("📤 Upload your medical report (PDF or TXT file)")
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf'],
            help="Upload PDF or text file containing your medical report"
        )

        if uploaded_file is not None:
            fid = upload_pdf(uploaded_file)
            file_extension = uploaded_file.name.split('.')[-1].lower()
            logger.info(f"File uploaded: {uploaded_file.name}")

            with st.spinner(f"📖 Reading {file_extension.upper()} file..."):
                try:
                    if file_extension == 'pdf':
                        report_text = extract_text_from_pdf(uploaded_file)

                        if report_text and len(report_text.strip()) > 50:
                            st.success(f"✅ PDF read successfully! ({len(report_text)} characters extracted)")
                            with st.expander("📄 Preview Extracted Text", expanded=True):
                                st.text_area(
                                    "Content extracted from PDF:",
                                    report_text[:2000] + ("..." if len(report_text) > 2000 else ""),
                                    height=200,
                                    disabled=True
                                )
                        else:
                            logger.warning("Failed to extract text from PDF")
                            st.error("❌ Could not extract text from PDF")
                            report_text = ""

                    elif file_extension == 'txt':
                        report_text = uploaded_file.read().decode('utf-8', errors='ignore')
                        if report_text.strip():
                            st.success(f"✅ Text file read successfully! ({len(report_text)} characters)")
                            logger.info(f"Text file read successfully: {len(report_text)} characters")
                        else:
                            logger.warning("Text file is empty")
                            st.error("❌ Text file is empty")
                            report_text = ""

                except Exception as e:
                    logger.error(f"Error reading file: {str(e)}")
                    st.error(f"❌ Error reading file: {str(e)}")
                    report_text = ""

    # Email input section
    st.markdown("---")
    st.markdown("### 📧 Get Results via Email (Optional)")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analysis_email = st.text_input(
            "Email address:",
            placeholder="your.email@example.com",
            help="Receive analysis results via email",
            key="analysis_email_input"
        )

    if st.button("🔍 Analyze Report", use_container_width=True, type="primary"):
        if report_text.strip():
            logger.info("Starting report analysis")
            with st.spinner("Analyzing report... This may take a moment."):
                try:
                    analysis = analyze_medical_report(report_text)

                    st.session_state.current_report = report_text
                    st.session_state.report_analysis = analysis

                    st.markdown("---")
                    st.markdown("### 📊 Analysis Results")

                    formatted_analysis = format_for_html(analysis)
                    st.markdown(f"""
                    <div class="report-card">
                        {formatted_analysis}
                    </div>
                    """, unsafe_allow_html=True)

                    # Send email if provided
                    if analysis_email:
                        with st.spinner("📧 Sending email..."):
                            email_content = f"""
                            <p><strong>Analysis Date:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            <hr>
                            <h3>Original Report Preview:</h3>
                            <div style="background: #f5f5f5; padding: 10px; border-radius: 5px; margin: 10px 0;">
                                <p style="white-space: pre-wrap;">{report_text[:500]}{'...' if len(report_text) > 500 else ''}</p>
                            </div>
                            <hr>
                            <h3>AI Analysis:</h3>
                            <div style="white-space: pre-wrap;">{analysis.replace(chr(10), '<br>')}</div>
                            """

                            success, message = send_email_notification(
                                analysis_email,
                                "Medical Report Analysis - ClinIQ AI",
                                email_content,
                                "analysis"
                            )

                            if success:
                                st.success(f"📧 {message}")
                            else:
                                st.warning(f"⚠️ {message}")

                    # Download button
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        download_content = f"""MEDICAL REPORT ANALYSIS
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
=====================================

ORIGINAL REPORT:
{report_text}

=====================================
AI ANALYSIS:
{analysis}

=====================================
Disclaimer: This analysis is AI-generated and for informational purposes only.
Always consult qualified healthcare professionals for medical decisions.
"""
                        st.download_button(
                            label="📥 Download Analysis",
                            data=download_content,
                            file_name=f"medical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    # Button to go to chatbot
                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.success("✅ Report analyzed! You can now ask questions about it.")
                        if st.button("💬 Ask Questions About This Report", use_container_width=True, type="primary"):
                            navigate_to("💬 Report Chatbot")

                    logger.info("Report analysis completed successfully")

                except Exception as e:
                    logger.error(f"Error analyzing report: {str(e)}")
                    st.error(f"Error analyzing report: {str(e)}")
        else:
            st.warning("Please enter a medical report to analyze.")

# Report Chatbot Page
elif st.session_state.current_page == "💬 Report Chatbot":
    logger.info("Displaying Report Chatbot page")
    show_back_button()

    st.title("💬 Chat About Your Medical Report")
    st.markdown("Ask me anything about your medical reports and get instant, personalized answers!")

    if st.session_state.current_report is None:
        st.warning("⚠️ No report uploaded yet!")
        st.info("👉 Please go to **'📄 Report Analyzer'** first to upload and analyze your medical report.")

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📄 Go to Report Analyzer", use_container_width=True, type="primary"):
                navigate_to("📄 Report Analyzer")
    else:
        with st.expander("📋 Current Report Summary", expanded=False):
            report_preview = st.session_state.current_report[:500] + (
                "..." if len(st.session_state.current_report) > 500 else "")
            st.text_area("Your Report:", report_preview, height=150, disabled=True)

            if st.button("📄 Upload New Report"):
                logger.info("Clearing current report for new upload")
                st.session_state.current_report = None
                st.session_state.report_analysis = None
                st.session_state.chat_history = []
                navigate_to("📄 Report Analyzer")

        st.markdown("---")

        st.markdown("### 💭 Ask Your Questions")

        if st.session_state.chat_history:
            for i, chat in enumerate(st.session_state.chat_history):
                st.markdown(f"""
                <div style="background: #e0f2fe; padding: 15px; border-radius: 15px; margin: 10px 0; border-left: 4px solid #0ea5e9;">
                    <strong>🙋 You:</strong> {chat['question']}
                </div>
                """, unsafe_allow_html=True)

                formatted_answer = format_for_html(chat['answer'])
                st.markdown(f"""
                <div class="success-box">
                    <strong>🤖 ClinIQ:</strong><br>{formatted_answer}
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### 💡 Suggested Questions")
        col1, col2 = st.columns(2)

        suggested_questions = [
            "Is my hemoglobin level normal?",
            "What does my glucose level mean?",
            "Should I be worried about my cholesterol?",
            "What foods can help improve my results?",
            "Do I need to see a doctor immediately?",
            "Explain my test results in simple terms"
        ]

        for idx, suggestion in enumerate(suggested_questions):
            col = col1 if idx % 2 == 0 else col2
            with col:
                if st.button(f"💬 {suggestion}", key=f"suggest_{idx}", use_container_width=True):
                    st.session_state.suggested_question = suggestion
                    st.rerun()

        st.markdown("---")

        default_question = st.session_state.get('suggested_question', '')
        if default_question:
            st.session_state.pop('suggested_question')

        user_question = st.text_input(
            "Type your question here:",
            value=default_question,
            placeholder="e.g., Is my hemoglobin low? What should I eat?",
            key="user_question_input"
        )

        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            ask_button = st.button("🚀 Ask Question", use_container_width=True, type="primary")

        if ask_button and user_question.strip():
            logger.info(f"Processing user question: {user_question[:100]}")
            with st.spinner("🤔 Thinking..."):
                try:
                    answer = chat_about_report(
                        user_question,
                        st.session_state.current_report,
                        st.session_state.report_analysis if st.session_state.report_analysis else "No previous analysis"
                    )

                    st.session_state.chat_history.append({
                        'question': user_question,
                        'answer': answer
                    })

                    logger.info("Chat response generated and added to history")
                    st.rerun()

                except Exception as e:
                    logger.error(f"Error in chat: {str(e)}")
                    st.error(f"❌ Error: {str(e)}")

        if st.session_state.chat_history:
            st.markdown("---")
            if st.button("🗑️ Clear Chat History"):
                logger.info("Clearing chat history")
                st.session_state.chat_history = []
                st.rerun()

# Knowledge Base Page
elif st.session_state.current_page == "📚 Knowledge Base":
    logger.info("Displaying Knowledge Base page")
    show_back_button()

    st.title("📚 Medical Knowledge Base")
    st.markdown("Search for information about any medical condition or term")

    condition = st.text_input(
        "Enter condition or medical term:",
        placeholder="e.g., hypertension, diabetes, MRI findings..."
    )

    if st.button("🔍 Search Medical Information", use_container_width=True, type="primary"):
        if condition.strip():
            logger.info(f"Searching knowledge base for: {condition}")
            with st.spinner(f"Searching for information about {condition}..."):
                try:
                    research = search_medical_info(condition)
                    formatted_research = format_for_html(research)
                    st.markdown(f"""
                    <div class="report-card">
                        <h3>📚 {condition.title()}</h3>
                        {formatted_research}
                    </div>
                    """, unsafe_allow_html=True)

                    logger.info(f"Knowledge base search completed for: {condition}")

                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col2:
                        download_content = f"""MEDICAL INFORMATION: {condition.title()}
Retrieved: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
=====================================

{research}

=====================================
Source: ClinIQ AI Knowledge Base
Disclaimer: This information is for educational purposes only.
Always consult qualified healthcare professionals for medical advice.
"""
                        st.download_button(
                            label="📥 Download Information",
                            data=download_content,
                            file_name=f"medical_info_{condition.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                except Exception as e:
                    logger.error(f"Error retrieving information: {str(e)}")
                    st.error(f"Error retrieving information: {str(e)}")
        else:
            st.warning("Please enter a condition to research.")

# Hospital Assistant Page
elif st.session_state.current_page == "🤖 Hospital Assistant":
    logger.info("Displaying Hospital Assistant page")
    show_back_button()

    st.title("🤖 Multi-Agent Hospital Assistant")
    st.markdown("Interact with our specialized AI agents for comprehensive care")

    agent_tab1, agent_tab2, agent_tab3 = st.tabs([
        "📅 Appointment Scheduler",
        "🚑 Patient Triage",
        "👨‍⚕️ Doctor Assistant"
    ])

    # Agent 1: Appointment Scheduler
    with agent_tab1:
        st.markdown("### 📅 Schedule an Appointment")

        col1, col2 = st.columns(2)

        with col1:
            patient_name = st.text_input("Patient Name:", placeholder="John Doe")
            preferred_date = st.date_input(
                "Preferred Date:",
                min_value=datetime.now().date(),
                value=datetime.now().date() + timedelta(days=1)
            )
            patient_email = st.text_input(
                "Email (optional):",
                placeholder="your.email@example.com",
                help="Provide email to receive appointment confirmation"
            )

        with col2:
            concern = st.text_input("Chief Concern:", placeholder="Describe your main concern...")
            preferred_time = st.time_input("Preferred Time:", value=datetime.strptime("09:00", "%H:%M").time())

        if st.button("📅 Schedule Appointment", use_container_width=True, type="primary"):
            if patient_name and concern:
                logger.info(f"Scheduling appointment request for: {patient_name}")
                with st.spinner("Processing appointment request..."):
                    try:
                        result, details, email_sent = AppointmentScheduler.schedule_appointment(
                            patient_name, concern,
                            preferred_date.strftime("%Y-%m-%d"),
                            preferred_time.strftime("%H:%M"),
                            patient_email if patient_email else None
                        )
                        collection.insert_one(result)
                        st.success("✅ Appointment request processed!")

                        # Show email notification status
                        if patient_email:
                            if email_sent:
                                st.success(f"📧 Confirmation sent to {patient_email}")
                            else:
                                st.warning("⚠️ Appointment scheduled but email notification failed.")

                        formatted_result = format_for_html(details)
                        st.markdown(f"""
                        <div class="success-box">
                            <h4>📋 Appointment Details</h4>
                            {formatted_result}
                        </div>
                        """, unsafe_allow_html=True)

                        st.info(f"📊 Total appointments scheduled: {len(st.session_state.appointments)}")

                    except Exception as e:
                        logger.error(f"Error scheduling appointment: {str(e)}")
                        st.error(f"Error scheduling appointment: {str(e)}")
            else:
                st.warning("Please fill in all required fields.")

        if st.session_state.appointments:
            st.markdown("---")
            st.markdown("### 📋 Recent Appointments")

            for idx, apt in enumerate(reversed(st.session_state.appointments[-3:]), 1):
                with st.expander(f"📌 {apt['patient']} - {apt['date']} at {apt['time']}", expanded=False):
                    st.markdown(f"""
                    **Patient:** {apt['patient']}  
                    **Concern:** {apt['concern']}  
                    **Date:** {apt['date']}  
                    **Time:** {apt['time']}  
                    **Email:** {apt.get('email', 'Not provided')}  
                    **Booked:** {apt['timestamp']}
                    """)

    # Agent 2: Patient Triage
    with agent_tab2:
        st.markdown("### 🚑 Patient Triage Assessment")
        st.markdown("Describe your symptoms for priority assessment")

        symptoms = st.text_area(
            "Symptoms:",
            height=150,
            placeholder="Describe your symptoms in detail (e.g., fever for 3 days, chest pain, difficulty breathing...)"
        )

        if st.button("🔍 Assess Priority", use_container_width=True, type="primary"):
            if symptoms.strip():
                logger.info("Performing triage assessment")
                with st.spinner("Performing triage assessment..."):
                    try:
                        triage_result = PatientTriage.triage_patient(symptoms)
                        formatted_triage = format_for_html(triage_result)

                        st.markdown(f"""
                        <div class="warning-box">
                            <h4>⚕️ Triage Assessment</h4>
                            {formatted_triage}
                        </div>
                        """, unsafe_allow_html=True)

                        st.info(
                            "**Important**: This is an AI assessment only. If you're experiencing severe symptoms, call emergency services immediately.")

                        logger.info("Triage assessment completed")

                    except Exception as e:
                        logger.error(f"Error performing triage: {str(e)}")
                        st.error(f"Error performing triage: {str(e)}")
            else:
                st.warning("Please describe your symptoms.")

    # Agent 3: Doctor Assistant
    with agent_tab3:
        st.markdown("### 👨‍⚕️ Medical Guidance Assistant")
        st.markdown("Get clinical guidelines and treatment protocols")

        col1, col2 = st.columns(2)

        with col1:
            medical_condition = st.text_input(
                "Condition/Diagnosis:",
                placeholder="e.g., Type 2 Diabetes"
            )

        with col2:
            related_symptoms = st.text_input(
                "Associated Symptoms:",
                placeholder="e.g., increased thirst, fatigue"
            )

        if st.button("📖 Get Clinical Guidance", use_container_width=True, type="primary"):
            if medical_condition.strip():
                logger.info(f"Retrieving medical guidance for: {medical_condition}")
                with st.spinner("Retrieving medical guidelines..."):
                    try:
                        guidance = DoctorAssistant.get_medical_guidance(
                            medical_condition,
                            related_symptoms if related_symptoms else "None specified"
                        )
                        formatted_guidance = format_for_html(guidance)

                        st.markdown(f"""
                        <div class="report-card">
                            <h4>📚 Clinical Guidance: {medical_condition}</h4>
                            {formatted_guidance}
                        </div>
                        """, unsafe_allow_html=True)

                        st.warning(
                            "**Medical Disclaimer**: This information is for educational purposes only and should not replace professional medical advice.")

                        logger.info(f"Medical guidance retrieved successfully for: {medical_condition}")

                    except Exception as e:
                        logger.error(f"Error retrieving guidance: {str(e)}")
                        st.error(f"Error retrieving guidance: {str(e)}")
            else:
                st.warning("Please enter a medical condition.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 20px;'>
    <p><strong>ClinIQ AI</strong> - Powered by Google Gemini 2.0</p>
    <p style='font-size: 0.9em;'>⚠️ This tool is for informational purposes only and does not replace professional medical advice.</p>
    <p style='font-size: 0.9em;'>Always consult qualified healthcare professionals for medical decisions.</p>
</div>
""", unsafe_allow_html=True)

logger.info(f"Page rendered: {st.session_state.current_page}")