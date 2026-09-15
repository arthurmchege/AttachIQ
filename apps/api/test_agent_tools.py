import asyncio
from database import get_db
from agent_tools import get_student_profile, get_pending_units, get_competency_detail, get_student_evidence
async def main():
    # Get a database session manually ( not via fastAPI, Depends this time)
    async for db in get_db():
        # Test 1: A real student who currently has no programme set
        result = await get_student_profile("3776de48-b964-4cc0-b1e5-73bce58f6b8b", db)
        print("Test 1 (Aaron no programme):", result)

        # Test 2: An invalid uuid format
        result = await get_student_profile("not-a-real-uuid", db)
        print("Test 2 (Invalid UUID):", result)

        # Test 3: a UUID that's syntactically valid but does not exist in the database
        result = await get_student_profile("00000000-0000-0000-0000-000000000000", db)
        print("Test 3 (Non-existent UUID):", result)

        # Test 4: get_pending_units — a real student with a programme and placement,
        # no assessments yet, so all 5 CSC units should come back as pending
        result = await get_pending_units("3776de48-b964-4cc0-b1e5-73bce58f6b8b", db)
        print("Test 4 (Aaron, all units pending):", result)

        # Test 5: get_pending_units — invalid UUID format
        result = await get_pending_units("not-a-real-uuid", db)
        print("Test 5 (Invalid UUID):", result)

        # Test 6: get_pending_units — syntactically valid UUID, not in the database
        result = await get_pending_units("00000000-0000-0000-0000-000000000000", db)
        print("Test 6 (Non-existent UUID):", result)

        # Test 7: get_competency_detail — a real competency unit (CSC101)
        result = await get_competency_detail("33fc6a6d-743c-4314-933f-2445dc0a004b", db)
        print("Test 7 (CSC101 detail):", result)

        # Test 8: get_competency_detail — invalid UUID format
        result = await get_competency_detail("not-a-real-uuid", db)
        print("Test 8 (Invalid UUID):", result)

        # Test 9: get_competency_detail — syntactically valid UUID, not in the database
        result = await get_competency_detail("00000000-0000-0000-0000-000000000000", db)
        print("Test 9 (Non-existent UUID):", result)

        # Test 10: get_student_evidence — Aaron's evidence for CSC101 (should return 1 item)
        result = await get_student_evidence(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            db
        )
        print("Test 10 (Aaron's CSC101 evidence):", result)

        # Test 11: get_student_evidence — Aaron has no evidence for a unit he hasn't submitted to
        # (any other CSC unit ID works here — pick one from your seed output that isn't CSC101)
        result = await get_student_evidence(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "a7be751d-8ff3-4718-8645-96fa0eb31151",  # CSC102
            db
        )
        print("Test 11 (Aaron, no evidence for CSC102):", result)

        # Test 12: get_student_evidence — invalid UUID format
        result = await get_student_evidence("not-a-real-uuid", "also-not-real", db)
        print("Test 12 (Invalid UUIDs):", result)

        # Test 13: get_student_evidence — student with no placement at all (non-existent student)
        result = await get_student_evidence(
            "00000000-0000-0000-0000-000000000000",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            db
        )
        print("Test 13 (Non-existent student):", result)

if __name__ == "__main__":
    asyncio.run(main())
