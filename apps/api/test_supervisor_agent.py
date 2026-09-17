import asyncio
from dotenv import load_dotenv

load_dotenv()

from database import get_db
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from supervisor_agent import build_supervisor_agent


async def main():
    async for db in get_db():
        agent = build_supervisor_agent(db)
        session_service = InMemorySessionService()
        session = await session_service.create_session(
            app_name="attachiq_supervisor",
            user_id="test_supervisor",
        )
        runner = Runner(
            agent=agent,
            app_name="attachiq_supervisor",
            session_service=session_service,
        )

        print("SupervisorIQ is ready. Type your messages below. Type 'exit' to quit.\n")
        print("Tip: try starting with something like:")
        print("  \"I am ready to assess Aaron Minish, student ID 3776de48-b964-4cc0-b1e5-73bce58f6b8b\"\n")

        while True:
            user_input = input("YOU: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break

            message = types.Content(role="user", parts=[types.Part(text=user_input)])

            try:
                async for event in runner.run_async(
                    user_id="test_supervisor",
                    session_id=session.id,
                    new_message=message,
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            print("\nSUPERVISORIQ:", event.content.parts[0].text, "\n")
                        else:
                            print("\nSUPERVISORIQ: (no response content — the model call may have failed)\n")
            except Exception as e:
                print(f"\nSUPERVISORIQ: Sorry, something went wrong talking to the model ({type(e).__name__}). "
                      f"Try sending that again.\n")


if __name__ == "__main__":
    asyncio.run(main())