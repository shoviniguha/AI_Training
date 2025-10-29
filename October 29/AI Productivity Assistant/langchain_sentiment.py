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
# 3. Sentiment Analyzer Tool with Detailed Explanation
# ------------------------------------------------------------
def sentiment_analyzer(text):

    # Construct the detailed prompt for sentiment analysis
    prompt_text = f"Please analyze the sentiment of the following text and classify it as Positive, Neutral, or Negative. Then provide a brief explanation for the classification (e.g., 'positive — happiness detected', 'negative — frustration or stress detected').\n\n{text}\n\nAnswer with the sentiment and the explanation."

    # Invoke the model with the sentiment analysis prompt
    result = llm.invoke(prompt_text)

    # Return the sentiment result with explanation, ensuring to strip any extra whitespace
    return result.content.strip()


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

    # Handle Sentiment Analysis command
    if user_input.lower().startswith("analyze"):
        try:
            # Extract the text after the command
            passage = " ".join(user_input.split()[1:]).strip()

            # Analyze the sentiment using the sentiment analyzer
            sentiment = sentiment_analyzer(passage)

            # Ensure that we have a valid sentiment result
            if sentiment:
                # Create a chat response in the format of agent's message
                agent_response = f"Agent: The sentiment is {sentiment}"

                # Print the sentiment analysis result
                print(agent_response)
            else:
                print("Agent: Could not determine the sentiment. Please try again.")
            continue
        except Exception as e:
            print(f"Agent: Error during sentiment analysis: {e}")
            continue

    # Default: use LLM for other queries
    try:
        response = llm.invoke(user_input)
        print("Agent:", response.content)
    except Exception as e:
        print("Error:", e)
