import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
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
# 4. Initialize memory
# ------------------------------------------------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ------------------------------------------------------------
# 5. NoteKeeper Tool Implementation
# ------------------------------------------------------------
notes = []


def store_note(note_text):
    notes.append(note_text)
    # Save the note into the conversation memory
    memory.save_context({"input": "note"}, {"output": note_text})  # Correctly pass inputs and outputs as arguments
    return f"Agent: Noted: \"{note_text}\""


def retrieve_notes():
    if not notes:
        return "Agent: You currently have no notes."
    else:
        return f"Agent: You currently have {len(notes)} note{'s' if len(notes) > 1 else ''}: " + " | ".join(notes)


# ------------------------------------------------------------
# 6. Conversational loop
# ------------------------------------------------------------
print("\n=== Start chatting with your Agent ===")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("\nConversation ended.")
        break

    # Handle Note storage command
    if user_input.lower().startswith("note"):
        note_text = " ".join(user_input.split()[1:]).strip()
        if note_text:
            # Store the note and give confirmation
            response = store_note(note_text)
            print(response)
        else:
            print("Agent: Please provide a note text.")
        continue

    # Handle Get notes command
    if user_input.lower() == "get notes":
        response = retrieve_notes()
        print(response)
        continue

    # Default: use LLM for other queries
    try:
        response = llm.invoke(user_input)
        print("Agent:", response.content)
        memory.save_context(user_input, response.content)  # Correctly save the context
    except Exception as e:
        print("Error:", e)
