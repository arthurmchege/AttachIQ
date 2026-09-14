import asyncio
from database import get_db
from agent_tools import get_student_profile, get_pending_units, get_competency_detail
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

        # Test 4: get_pending_units — a real student with a programme and placement,
        # no assessments yet, so all 5 CSC units should come back as pending
        result = await get_pending_units("35339b32-81ad-498b-a858-44cfeed48ddf", db)
        print("Test 4 (Aaron, all units pending):", result)

        # Test 5: get_pending_units — invalid UUID format
        result = await get_pending_units("not-a-real-uuid", db)
        print("Test 5 (Invalid UUID):", result)

        # Test 6: get_pending_units — syntactically valid UUID, not in the database
        result = await get_pending_units("00000000-0000-0000-0000-000000000000", db)
        print("Test 6 (Non-existent UUID):", result)

        # Test 7: get_competency_detail — a real competency unit (CSC101)
        result = await get_competency_detail("1c39bcd8-45f9-4f9d-98c0-3e3b89b75918", db)
        print("Test 7 (CSC101 detail):", result)

        # Test 8: get_competency_detail — invalid UUID format
        result = await get_competency_detail("not-a-real-uuid", db)
        print("Test 8 (Invalid UUID):", result)

        # Test 9: get_competency_detail — syntactically valid UUID, not in the database
        result = await get_competency_detail("00000000-0000-0000-0000-000000000000", db)
        print("Test 9 (Non-existent UUID):", result)

if __name__ == "__main__":
    asyncio.run(main())
