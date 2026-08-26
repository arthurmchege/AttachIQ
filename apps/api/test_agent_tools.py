import asyncio
from database import get_db
from agent_tools import get_student_profile

async def main():
    # Get a database session manually ( not via fastAPI, Depends this time)
    async for db in get_db():
        # Test 1: A real student who currently has no programme set
        result = await get_student_profile("35339b32-81ad-498b-a858-44cfeed48ddf", db)
        print("Test 1 (Aaron no programme):", result)

        # Test 2: An invalid uuid format
        result = await get_student_profile("not-a-real-uuid", db)
        print("Test 2 (Invalid UUID):", result)

        # Test 3: a UUID that's syntactically valid but does not exist in the database
        result = await get_student_profile("00000000-0000-0000-0000-000000000000", db)
        print("Test 3 (Non-existent UUID):", result)

if __name__ == "__main__":
    asyncio.run(main())
