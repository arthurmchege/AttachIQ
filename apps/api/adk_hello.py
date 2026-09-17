import asyncio
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Step 1: Defining the agent. (inert config does nothing yet)
hello_agent = Agent(
  name="hello_agent",
  model="gemini-3.5-flash",
  description="A minimal agent to confirm adk is wired up correctly",
  instruction="You are a friendly assistant.Keep response short.",
)

async def main():
  # Create a session service to manage sessions in memory
  session_service = InMemorySessionService()

  session = await session_service.create_session(
    app_name="attachiq_hello",
    user_id="test_user",
  )

  # Creating a runner to run the agent
  runner = Runner(
    agent=hello_agent,
    app_name="attachiq_hello",
    session_service=session_service,
  )

  # Send a message to the agent
  user_message = types.Content(
    role="user", parts=[types.Part(text="Hello!, Who are you?")]
  )

  # This is what actually kicks of the loop and sends the message to gemini-3.5-flash until a response comes back.
  async for event in runner.run_async(
    user_id="test_user",
    session_id=session.id,
    new_message=user_message,
  ):
    if event.is_final_response():
      if event.content and event.content.parts:
        print("AGENT SAID:", event.content.parts[0].text)
      else:
        print("AGENT ERROR: No response content — the model call may have failed.")
        if hasattr(event, "error_message") and event.error_message:
          print("Details:", event.error_message)

if __name__ == "__main__":
  asyncio.run(main())