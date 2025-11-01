import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

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
# 3. Define helper tools
# ------------------------------------------------------------
def count(inp: str) -> int:
    lst=inp.split(" ")
    return len(lst)

def reverse(inp: str) -> str:
    lst=inp.split(" ")
    return " ".join(lst[::-1])
def synonym(word: str) -> str:
    prompt_text = ChatPromptTemplate.from_template(
        f"<s>[INST] You are a concise assistant. Give a short definition of the following word in 1 or 2 sentences: {word}[/INST]"
    )

    # Render the prompt to a string
    formatted_prompt = prompt_text.format()

    # Invoke the model with the formatted prompt
    result = llm.invoke(formatted_prompt)

    # Return the priority result (make sure to strip any extra whitespace)
    return result.content.strip()

# ------------------------------------------------------------
# 4. Initialize memory
# ------------------------------------------------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
# ------------------------------------------------------------
# 5. Conversational loop
# ------------------------------------------------------------
print("\n=== Start chatting with your Agent ===")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()
    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # Handle Multiply command
    if user_input.lower().startswith("count"):
        try:
            sentence = " ".join(user_input.split()[1:]).strip()  # Extract task text
            cnt = count(sentence)
            res=f"Agent: Your sentence has {cnt} words."
            print(res)
            memory.save_context({"input": user_input}, {"output": res})
            continue
        except Exception as e:
            print(f"Agent: Error: {e}")
            continue
    if user_input.lower().startswith("reverse"):
        try:
            sentence = " ".join(user_input.split()[1:]).strip()  # Extract task text
            rev = reverse(sentence)
            print(f"Agent: {rev}")
            memory.save_context({"input": user_input}, {"output": rev})
            continue
        except Exception as e:
            print(f"Agent: Error: {e}")
            continue
    if user_input.lower().startswith("define"):
        try:
            word = " ".join(user_input.split()[1:]).strip()  # Extract task text
            meaning = synonym(word)
            print(f"Agent: {meaning}")
            memory.save_context({"input": user_input}, {"output": meaning})
            continue
        except Exception as e:
            print(f"Agent: Error: {e}")
            continue
    # Default: use LLM for other queries
    try:
        response = llm.invoke(user_input)
        print("Agent:", response.content)
        memory.save_context({"input": user_input}, {"output": response.content})
    except Exception as e:
        print("Error:", e)