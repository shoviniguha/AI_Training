# Import the dependencies
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os
import asyncio

# Load the environment variables
# You should always use a .env file to store your API keys
load_dotenv()

# Create the open router model client
open_router_model_client = OpenAIChatCompletionClient(
    base_url="https://openrouter.ai/api/v1",
    model="mistralai/mistral-7b-instruct:free",
    api_key="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",
    model_info={
        "family": "openai",
        "vision": True,
        "function_calling": True,
        "json_output": False
    }
)

# Create an Agent using the open router model client created in previous step
assistant = AssistantAgent(
    name="myassistent",
    model_client=open_router_model_client,
    system_message="You are a helpful assistant that answers questions accurately and concisely."
)

# Ask any question to your agent and see the result
async def main() -> None:
    result = await assistant.run(task="What is the capital of India?")
    print(f"Result: {result.messages[-1].content}")

asyncio.run(main())