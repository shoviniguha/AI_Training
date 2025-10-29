import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# ------------------------------------------------------------
# 1. Load environment variables
# ------------------------------------------------------------
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env file")

# ------------------------------------------------------------
# 2. Initialize the Mistral model via OpenRouter
# ------------------------------------------------------------
llm = ChatOpenAI(
    model="mistralai/mistral-7b-instruct",
    temperature=0.4,
    max_tokens=256,
    api_key=api_key,
    base_url=base_url,
)


# ------------------------------------------------------------
# 3. Task Priority Classifier
# ------------------------------------------------------------

def classify_with_llm(task):
    prompt_text = ChatPromptTemplate.from_template(
        f"<s>[INST] Classify the priority of the following task as HIGH, MEDIUM, or LOW. Just answer with HIGH, MEDIUM, or LOW: {task}[/INST]"
    )

    # Render the prompt to a string
    formatted_prompt = prompt_text.format()

    # Invoke the model with the formatted prompt
    result = llm.invoke(formatted_prompt)

    # Return the priority result (make sure to strip any extra whitespace)
    return result.content.strip()


# ------------------------------------------------------------
# 4. Conversational loop
# ------------------------------------------------------------
print("\n=== Start chatting with your Agent ===")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # Handle Task Priority classification command
    if user_input.lower().startswith("priority"):
        try:
            task = " ".join(user_input.split()[1:]).strip()  # Extract task text
            priority = classify_with_llm(task)
            print(f"Agent: Task \"{task}\" marked as {priority} priority.")
            continue
        except Exception as e:
            print(f"Agent: Error during priority classification: {e}")
            continue

    # Default: use LLM for other queries
    try:
        response = llm.invoke(user_input)
        print("Agent:", response.content)
    except Exception as e:
        print("Error:", e)
