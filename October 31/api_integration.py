import requests
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
import litellm

# ---------------------------------------------------------------------
# 1. Load environment variables
# ---------------------------------------------------------------------
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
# ---------------------------------------------------------------------
# 2. Configure LiteLLM globally for OpenRouter
# ---------------------------------------------------------------------
litellm.api_key = os.getenv("OPENROUTER_API_KEY")
litellm.api_base = "https://openrouter.ai/api/v1"
model_name = "openrouter/mistralai/mistral-7b-instruct"

def fetch_weather(city:str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    response = requests.get(url)
    weather=response.json()
    keys = ['city', 'temperature', 'humidity', 'description']
    city=weather['name']
    temperature=weather['main']['temp']
    humidity=weather['main']['humidity']
    description=weather['weather'][0]['description']
    values=[city,temperature,humidity,description]
    conditions=dict(zip(keys,values))
    return conditions

litellm.api_key = os.getenv("OPENROUTER_API_KEY")
litellm.api_base = "https://openrouter.ai/api/v1"
model_name = "openrouter/mistralai/mistral-7b-instruct"

planner = Agent(
    role="Weather Reporter",
    goal="Summarize the weather.",
    backstory="A reporter who can create weather reports.",
    allow_delegation=True,
    llm=model_name,
)
plan_task = Task(
    description="Extract the weather from the dictionary and report it like a weather reporter. Mention the city name.",
    expected_output="A concise weather report.",
    agent=planner,
)
crew = Crew(
    agents=[planner],
    tasks=[plan_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    topic = fetch_weather("Los Angeles")
    print(topic)
    print(f"\n--- Running CrewAI Planner–Specialist Workflow ---\nTopic: {topic}\n")
    result = crew.kickoff(inputs={"topic": topic})
    print("\n--- FINAL OUTPUT ---\n")
    print(result)
