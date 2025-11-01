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
    role="Marketing Planner",
    goal="Create a 3-step marketing plan, including objectives, target audience, and strategies.",
    backstory="A creative AI strategist who designs marketing plans for successful campaigns.",
    allow_delegation=True,
    llm=model_name,
)

specialist = Agent(
    role="Marketing Specialist",
    goal="Execute the Marketing Planner’s plan and summarize campaign results, including key metrics.",
    backstory="A detail-oriented AI marketer who implements marketing campaigns and analyzes results.",
    llm=model_name,
)

# ---------------------------------------------------------------------
# 4. Define Tasks
# ---------------------------------------------------------------------
plan_task = Task(
    description="Given a product or service, create a 3-step marketing campaign plan with objectives, target audience, and strategies.",
    expected_output="A structured marketing plan with 3 steps, each containing an objective, target audience, and strategy.",
    agent=planner,
)

execute_task = Task(
    description="Take the Planner’s marketing plan and summarize the campaign results, including key metrics such as engagement and ROI.",
    expected_output="A 3-point summary explaining the outcomes of the campaign for each step, including metrics.",
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
    topic = "Launching a new line of eco-friendly skincare products"
    print(f"\n--- Running CrewAI Marketing Planner–Specialist Workflow ---\nTopic: {topic}\n")
    result = crew.kickoff(inputs={"topic": topic})
    print("\n--- FINAL OUTPUT ---\n")
    print(result)
