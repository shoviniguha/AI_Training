from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from datetime import datetime
from pathlib import Path

load_dotenv()

app = FastAPI()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# History file path
HISTORY_FILE = "qa-history.json"


class Prompt(BaseModel):
    question: str = Field(..., min_length=1, description="Question cannot be empty")


def load_history():
    """Load Q&A history from file"""
    if Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_to_history(question, answer):
    """Save Q&A to history file"""
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer
    })
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


@app.post("/generate")
async def generate_response(prompt: Prompt):
    if not prompt.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

        print(f"Question received: {prompt.question}")  # Debug log

        client_router = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        response = client_router.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",
            messages=[
                {"role": "user", "content": f"Question: {prompt.question}\n\nAnswer:"}
            ],
        max_tokens = 500,
        temperature = 0.7
        )

        print(f"Full response: {response}")  # Debug log
        print(f"Response choices: {response.choices}")  # Debug log

        answer = response.choices[0].message.content
        print(f"Answer extracted: {answer}")  # Debug log

        # Save to history
        save_to_history(prompt.question, answer)

        return {
            "question": prompt.question,
            "response": answer
        }
    except Exception as e:
        print(f"Error occurred: {str(e)}")  # Debug log
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/history")
async def get_history():
    """Endpoint to retrieve Q&A history"""
    return load_history()