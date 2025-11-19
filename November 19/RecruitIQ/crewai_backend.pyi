"""
AI Talent Intelligence Platform - CrewAI Backend
Multi-agent system for recruitment automation
Adapted to use Gemini 2.5 Flash via LangChain's Google GenAI integration
"""

from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
import re
from dotenv import load_dotenv
import os
load_dotenv()

# ---------- LLM INITIALIZATION (Gemini 2.5 Flash) ----------
# Option A: rely on GOOGLE_API_KEY env var (preferred)
# export GOOGLE_API_KEY="your_api_key_here"

# Option B: pass key explicitly: ChatGoogleGenerativeAI(google_api_key="...")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
)

# ==================== AGENTS ====================

class RecruitmentAgents:
    """Define all recruitment agents"""

    def cv_parser_agent(self) -> Agent:
        """Agent specialized in parsing and extracting CV information"""
        return Agent(
            role='CV Parser & Analyzer',
            goal='Extract structured information from CVs including skills, experience, education, and achievements',
            backstory="""You are an expert CV parser with years of experience in 
            understanding various CV formats. You excel at extracting key information 
            and structuring it in a consistent format.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def skill_matcher_agent(self) -> Agent:
        """Agent specialized in matching skills to job requirements"""
        return Agent(
            role='Skills Matching Specialist',
            goal='Match candidate skills with job requirements and identify skill gaps',
            backstory="""You are a technical recruiter with deep knowledge of various 
            technologies and skills. You can identify skill matches, gaps, and assess 
            the transferability of skills across domains.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def experience_evaluator_agent(self) -> Agent:
        """Agent specialized in evaluating experience relevance"""
        return Agent(
            role='Experience Evaluator',
            goal='Assess the relevance and quality of candidate experience for the role',
            backstory="""You are a senior hiring manager who evaluates candidates 
            based on their experience quality, progression, and relevance to the role. 
            You understand industry standards and career trajectories.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def culture_fit_analyst_agent(self) -> Agent:
        """Agent specialized in culture fit assessment"""
        return Agent(
            role='Culture Fit Analyst',
            goal='Analyze candidate-team compatibility across communication, work style, and values',
            backstory="""You are an organizational psychologist specializing in 
            team dynamics and culture fit. You assess how well candidates will 
            integrate with existing team structures and work environments.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def interview_designer_agent(self) -> Agent:
        """Agent specialized in creating personalized interview questions"""
        return Agent(
            role='Interview Question Designer',
            goal='Create targeted, personalized interview questions based on candidate profile and role requirements',
            backstory="""You are an expert interviewer who designs questions that 
            reveal candidate capabilities, cultural fit, and potential. You create 
            questions that are specific to each candidate's background.""",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def hiring_decision_agent(self) -> Agent:
        """Agent that synthesizes all information into hiring recommendation"""
        return Agent(
            role='Hiring Decision Advisor',
            goal='Synthesize all assessment data into clear hiring recommendations',
            backstory="""You are a strategic hiring advisor who reviews all candidate 
            assessments and provides data-driven hiring recommendations. You balance 
            technical fit, culture fit, and growth potential.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )

# ... the rest of your classes (RecruitmentTasks, RecruitmentCrew, example usage)
# remain unchanged and will use the new `llm` instance above.