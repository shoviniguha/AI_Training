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


def transform_text(command):
    parts = command.split(" ", 1)  # Split into command and the rest of the text
    if len(parts) < 2:
        return "Agent: Please provide text to transform."
    action, text = parts
    if action.lower() == "upper":
        return text.upper()
    elif action.lower() == "lower":
        return text.lower()
    else:
        return "Invalid command. Please use 'upper' or 'lower'."
def repeat_text(command):
    parts = command.split(" ")
    if len(parts) < 2:
        return "Agent: Please provide text to repeat."
    action , word , itr = parts
    word=word+" "
    res= word * int(itr)
    return res


def show_history():
    """
    Displays the entire conversation history stored in ConversationBufferMemory.

    :return: A string representing the conversation history.
    """
    if not memory.buffer:
        return "Agent: No conversation history available."

    # Format the conversation history correctly by extracting the content of each message
    history = "\n".join([f"You: {entry.content}" if isinstance(entry, HumanMessage)
                         else f"Agent: {entry.content}"
                         for entry in memory.buffer])

    return history


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
    if user_input.lower().startswith(("upper","lower")):
        try:
            transf=transform_text(user_input)
            print(f"Agent: {transf}")
            memory.save_context({"input": user_input}, {"output": transf})
            continue
        except Exception as e:
            print(f"Agent: Error: {e}")
            continue
    if user_input.lower().startswith("repeat"):
        try:
            res=repeat_text(user_input)
            print(f"Agent: {res}")
            memory.save_context({"input": user_input}, {"output": res})
            continue
        except Exception as e:
            print(f"Agent: Error: {e}")
            continue
    if user_input.lower().startswith("history"):
        try:
            res=show_history()
            print(f"Agent: {res}")
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