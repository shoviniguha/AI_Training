"""
AI Talent Intelligence Platform - LangGraph Workflow
Advanced state management and conditional routing for recruitment
Adapted to use Google Gemini (google-genai) instead of Anthropic
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
import operator
import json
import os

# Google GenAI SDK
# Install with: pip install google-genai
from google import genai

# ==================== STATE DEFINITION ====================

class RecruitmentState(TypedDict):
    """State for the recruitment workflow"""
    # Input data
    cv_text: str
    job_description: str
    candidate_profile: Dict[str, int]
    team_profile: Dict[str, int]

    # Parsed data
    parsed_cv: Dict[str, Any]

    # Scores and assessments
    skill_match_score: float
    experience_score: float
    culture_fit_score: float
    overall_score: float

    # Detailed assessments
    skills_matched: List[str]
    skills_gap: List[str]
    strengths: List[str]
    concerns: List[str]

    # Interview questions
    interview_questions: List[Dict[str, str]]

    # Final recommendation
    recommendation: str
    hiring_brief: Dict[str, Any]

    # Control flow
    stage: str
    errors: List[str]


# ==================== LLM CLIENT & HELPER ====================

# Initialize Google GenAI client (reads GOOGLE_API_KEY env var if set)
def get_genai_client():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        return genai.Client(api_key=api_key)
    else:
        # If no key provided, client will rely on application default credentials
        return genai.Client()

_client = get_genai_client()

def call_gemini(prompt: str, model: str = "gemini-2.5-flash", max_output_tokens: int = 800, temperature: float = 0.7) -> str:
    """Call Gemini and return the generated text"""
    # The SDK's generate_content expects `contents` (a string prompt or list)
    resp = _client.models.generate_content(
        model=model,
        contents=prompt,
        max_output_tokens=max_output_tokens,
        temperature=temperature
    )
    # `resp` typically has a `.text` attribute (or str(resp) fallback)
    text = getattr(resp, "text", None)
    if not text:
        text = str(resp)
    return text


# ==================== NODE FUNCTIONS ====================

# (All node logic preserved; only LLM calls changed to call_gemini)

def parse_cv_node(state: RecruitmentState) -> RecruitmentState:
    """Parse CV and extract structured information"""
    print("📄 Parsing CV...")

    system_msg = "You are an expert CV parser. Extract structured information from CVs."
    human_msg = f"""Parse this CV and extract information in JSON format:

CV:
{state['cv_text']}

Extract:
- name
- contact (email, phone)
- skills (list)
- experience (list of jobs with company, role, duration, achievements)
- education (list)
- certifications (list)

Respond with valid JSON only."""

    prompt = system_msg + "\n\n" + human_msg

    try:
        response_text = call_gemini(prompt, max_output_tokens=800, temperature=0.2)

        # Extract JSON
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            parsed_cv = json.loads(response_text[start_idx:end_idx])
            state['parsed_cv'] = parsed_cv
            state['stage'] = 'cv_parsed'
        else:
            state['errors'].append("Failed to parse CV JSON")
    except Exception as e:
        state['errors'].append(f"CV parsing error: {str(e)}")

    return state


def skill_matching_node(state: RecruitmentState) -> RecruitmentState:
    """Match skills and calculate skill score"""
    print("🎯 Matching skills...")

    system_msg = "You are a technical recruiter expert in skill matching."
    human_msg = f"""Analyze skill match between candidate and job:

Candidate Skills:
{json.dumps(state.get('parsed_cv', {}).get('skills', []))}

Job Description:
{state['job_description']}

Provide JSON with:
- skillsMatched (list)
- skillsGap (list)
- matchScore (0-100)
- reasoning (string)

Respond with valid JSON only."""

    prompt = system_msg + "\n\n" + human_msg

    try:
        response_text = call_gemini(prompt, max_output_tokens=800, temperature=0.2)

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            result = json.loads(response_text[start_idx:end_idx])
            state['skills_matched'] = result.get('skillsMatched', [])
            state['skills_gap'] = result.get('skillsGap', [])
            state['skill_match_score'] = float(result.get('matchScore', 0))
            state['stage'] = 'skills_matched'
        else:
            state['errors'].append("Failed to parse skill matching JSON")
    except Exception as e:
        state['errors'].append(f"Skill matching error: {str(e)}")

    return state


def experience_evaluation_node(state: RecruitmentState) -> RecruitmentState:
    """Evaluate experience and calculate experience score"""
    print("💼 Evaluating experience...")

    system_msg = "You are a senior hiring manager evaluating candidate experience."
    human_msg = f"""Evaluate candidate's experience for this role:

Experience:
{json.dumps(state.get('parsed_cv', {}).get('experience', []))}

Job Requirements:
{state['job_description']}

Provide JSON with:
- experienceScore (0-100)
- yearsRelevant (number)
- strengths (list of strings)
- concerns (list of strings)

Respond with valid JSON only."""

    prompt = system_msg + "\n\n" + human_msg

    try:
        response_text = call_gemini(prompt, max_output_tokens=800, temperature=0.2)

        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx != -1 and end_idx > start_idx:
            result = json.loads(response_text[start_idx:end_idx])
            state['experience_score'] = float(result.get('experienceScore', 0))
            state['strengths'] = result.get('strengths', [])
            state['concerns'] = result.get('concerns', [])
            state['stage'] = 'experience_evaluated'
        else:
            state['errors'].append("Failed to parse experience evaluation JSON")
    except Exception as e:
        state['errors'].append(f"Experience evaluation error: {str(e)}")

    return state


def culture_fit_node(state: RecruitmentState) -> RecruitmentState:
    """Calculate culture fit score"""
    print("🤝 Analyzing culture fit...")

    # Get profiles
    candidate = state.get('candidate_profile', {})
    team = state.get('team_profile', {})

    # Calculate subscores
    async_score = 100 - abs(candidate.get('async_comfort', 3) - (6 - team.get('sync_level', 3))) * 20
    structure_score = 100 - abs(candidate.get('process_preference', 3) - team.get('process_need', 3)) * 20
    manager_score = 100 - abs(candidate.get('meeting_frequency', 3) - team.get('manager_style', 3)) * 20
    remote_score = 100 - abs(candidate.get('remote_preference', 3) - team.get('remote_required', 3)) * 20

    # Ensure scores are in valid range
    async_score = max(0, min(100, async_score))
    structure_score = max(0, min(100, structure_score))
    manager_score = max(0, min(100, manager_score))
    remote_score = max(0, min(100, remote_score))

    # Calculate weighted total
    culture_fit_score = (
            0.25 * async_score +
            0.35 * structure_score +
            0.20 * manager_score +
            0.20 * remote_score
    )

    state['culture_fit_score'] = round(culture_fit_score, 1)
    state['stage'] = 'culture_fit_calculated'

    return state


def calculate_overall_score_node(state: RecruitmentState) -> RecruitmentState:
    """Calculate overall candidate score"""
    print("📊 Calculating overall score...")

    # Weighted average of all scores
    skill_weight = 0.40
    experience_weight = 0.35
    culture_weight = 0.25

    overall = (
            skill_weight * state.get('skill_match_score', 0) +
            experience_weight * state.get('experience_score', 0) +
            culture_weight * state.get('culture_fit_score', 0)
    )

    state['overall_score'] = round(overall, 1)

    # Determine recommendation
    if overall >= 85:
        state['recommendation'] = "Strong Hire"
    elif overall >= 70:
        state['recommendation'] = "Hire"
    elif overall >= 55:
        state['recommendation'] = "Maybe - Further Assessment Needed"
    else:
        state['recommendation'] = "No Hire"

    state['stage'] = 'overall_calculated'

    return state


def generate_interview_questions_node(state: RecruitmentState) -> RecruitmentState:
    """Generate personalized interview questions"""
    print("❓ Generating interview questions...")

    system_msg = "You are an expert interview designer creating personalized questions."
    human_msg = f"""Generate 8 personalized interview questions for this candidate:

Job Description:
{state['job_description']}

Candidate Profile:
- Skills Matched: {', '.join(state.get('skills_matched', []))}
- Skills Gap: {', '.join(state.get('skills_gap', []))}
- Overall Score: {state.get('overall_score', 0)}
- Strengths: {', '.join(state.get('strengths', []))}
- Concerns: {', '.join(state.get('concerns', []))}

Create questions covering:
- Technical (3 questions)
- Behavioral (2 questions)
- Situational (2 questions)
- Culture fit (1 question)

Respond with JSON array:
[
  {{
    "question": "...",
    "category": "Technical/Behavioral/Situational/Culture",
    "purpose": "...",
    "follow_up": "..."
  }}
]

Valid JSON only."""

    prompt = system_msg + "\n\n" + human_msg

    try:
        response_text = call_gemini(prompt, max_output_tokens=1000, temperature=0.3)

        # Try to find JSON array
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        if start_idx != -1 and end_idx > start_idx:
            questions = json.loads(response_text[start_idx:end_idx])
            state['interview_questions'] = questions
        else:
            # Try object format
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                result = json.loads(response_text[start_idx:end_idx])
                state['interview_questions'] = result.get('questions', [])

        state['stage'] = 'questions_generated'
    except Exception as e:
        state['errors'].append(f"Question generation error: {str(e)}")

    return state


def create_hiring_brief_node(state: RecruitmentState) -> RecruitmentState:
    """Create comprehensive hiring decision brief"""
    print("📋 Creating hiring brief...")

    state['hiring_brief'] = {
        "candidate_name": state.get('parsed_cv', {}).get('name', 'Unknown'),
        "date": "2025-11-17",
        "overall_recommendation": state.get('recommendation'),
        "overall_score": state.get('overall_score'),
        "scores": {
            "skill_match": state.get('skill_match_score', 0),
            "experience": state.get('experience_score', 0),
            "culture_fit": state.get('culture_fit_score', 0)
        },
        "strengths": state.get('strengths', []),
        "concerns": state.get('concerns', []),
        "skills_matched": state.get('skills_matched', []),
        "skills_gap": state.get('skills_gap', []),
        "next_steps": [
            "Review hiring brief with hiring manager",
            "Schedule technical interview" if state.get('overall_score', 0) >= 60 else "Thank candidate for their time",
            "Conduct culture fit interview" if state.get('culture_fit_score', 0) >= 70 else "Assess team fit concerns"
        ]
    }

    state['stage'] = 'complete'

    return state


# ==================== CONDITIONAL ROUTING ====================

def should_continue_to_questions(state: RecruitmentState) -> str:
    """Decide if we should generate interview questions"""
    if state.get('overall_score', 0) >= 55:
        return "generate_questions"
    else:
        return "create_brief"


# ==================== BUILD GRAPH ====================

def create_recruitment_workflow() -> StateGraph:
    """Create the recruitment workflow graph"""

    workflow = StateGraph(RecruitmentState)

    # Add nodes
    workflow.add_node("parse_cv", parse_cv_node)
    workflow.add_node("match_skills", skill_matching_node)
    workflow.add_node("evaluate_experience", experience_evaluation_node)
    workflow.add_node("calculate_culture_fit", culture_fit_node)
    workflow.add_node("calculate_overall", calculate_overall_score_node)
    workflow.add_node("generate_questions", generate_interview_questions_node)
    workflow.add_node("create_brief", create_hiring_brief_node)

    # Add edges
    workflow.set_entry_point("parse_cv")
    workflow.add_edge("parse_cv", "match_skills")
    workflow.add_edge("match_skills", "evaluate_experience")
    workflow.add_edge("evaluate_experience", "calculate_culture_fit")
    workflow.add_edge("calculate_culture_fit", "calculate_overall")

    # Conditional routing
    workflow.add_conditional_edges(
        "calculate_overall",
        should_continue_to_questions,
        {
            "generate_questions": "generate_questions",
            "create_brief": "create_brief"
        }
    )

    workflow.add_edge("generate_questions", "create_brief")
    workflow.add_edge("create_brief", END)

    return workflow.compile()


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Create workflow
    app = create_recruitment_workflow()

    # Initial state
    initial_state = {
        "cv_text": """
        Jane Smith
        Senior Python Developer
        jane.smith@email.com | +1-555-0123

        EXPERIENCE:
        - Senior Python Developer at DataCorp (2019-Present)
          * Built data pipelines processing 10TB+ daily
          * Implemented microservices with FastAPI
          * Led team of 4 developers

        SKILLS:
        Python, FastAPI, Docker, PostgreSQL, AWS, React

        EDUCATION:
        M.S. Computer Science, Tech University (2019)
        """,
        "job_description": """
        Senior Backend Engineer needed for our data platform team.
        Requirements: Python, FastAPI, microservices, 5+ years experience.
        """,
        "candidate_profile": {
            "async_comfort": 4,
            "process_preference": 3,
            "meeting_frequency": 2,
            "remote_preference": 5
        },
        "team_profile": {
            "sync_level": 2,
            "manager_style": 3,
            "process_need": 3,
            "remote_required": 4
        },
        "stage": "initial",
        "errors": [],
        "skills_matched": [],
        "skills_gap": [],
        "strengths": [],
        "concerns": [],
        "interview_questions": []
    }

    # Run workflow
    print("🚀 Starting recruitment workflow...\n")
    result = app.invoke(initial_state)

    # Print results
    print("\n" + "=" * 50)
    print("RECRUITMENT WORKFLOW RESULTS")
    print("=" * 50)
    print(f"\nOverall Score: {result.get('overall_score', 0)}")
    print(f"Recommendation: {result.get('recommendation', 'N/A')}")
    print(f"\nSkills Matched: {len(result.get('skills_matched', []))}")
    print(f"Skills Gap: {len(result.get('skills_gap', []))}")
    print(f"Culture Fit Score: {result.get('culture_fit_score', 0)}")
    print(f"\nInterview Questions Generated: {len(result.get('interview_questions', []))}")

    if result.get('errors'):
        print(f"\n⚠️ Errors: {result['errors']}")

    print("\n✅ Workflow complete!")
    print(json.dumps(result.get('hiring_brief', {}), indent=2))