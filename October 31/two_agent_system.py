import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
import litellm

# ---------------------------------------------------------------------
# 1. Load environment variables
# ---------------------------------------------------------------------
load_dotenv()
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY")

# ---------------------------------------------------------------------
# 2. Configure LiteLLM globally for OpenRouter
# ---------------------------------------------------------------------
litellm.api_key = os.getenv("OPENROUTER_API_KEY")
litellm.api_base = "https://openrouter.ai/api/v1"
model_name = "openrouter/mistralai/mistral-7b-instruct"

# ---------------------------------------------------------------------
# 3. Define Agents
# ---------------------------------------------------------------------
planner = Agent(
    role="Planner",
    goal="Create a structured 3-step plan with goals and deliverables.",
    backstory="A strategic AI project planner who designs clear blueprints.",
    allow_delegation=True,
    llm=model_name,
)

specialist = Agent(
    role="Specialist",
    goal="Execute the Planner’s 3-step plan and summarize the results clearly.",
    backstory="A detail-oriented AI engineer capable of executing complex plans.",
    llm=model_name,
)

# ---------------------------------------------------------------------
# 4. Define Tasks
# ---------------------------------------------------------------------
plan_task = Task(
    description="Given the topic, create a 3-step plan with goals and deliverables.",
    expected_output="A structured plan with 3 steps, each having a goal and deliverable.",
    agent=planner,
)

execute_task = Task(
    description="Take the Planner’s 3-step plan and write a short summary of what was achieved.",
    expected_output="A 3-point summary explaining the outcomes for each step.",
    agent=specialist,
)

# ---------------------------------------------------------------------
# 5. Create and Run the Crew
# ---------------------------------------------------------------------
crew = Crew(
    agents=[planner, specialist],
    tasks=[plan_task, execute_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    topic = "Developing an AI-based document summarization system"
    print(f"\n--- Running CrewAI Planner–Specialist Workflow ---\nTopic: {topic}\n")
    result = crew.kickoff(inputs={"topic": topic})
    print("\n--- FINAL OUTPUT ---\n")
    print(result)
