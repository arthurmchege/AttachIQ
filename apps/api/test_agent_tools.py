import asyncio
from database import get_db
from agent_tools import get_student_profile, get_pending_units, get_competency_detail, get_student_evidence, draft_assessment, submit_assessment
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

        # Test 14: draft_assessment — a solid Mastery-level score
        result = await draft_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            85,
            "Aaron completed the task independently and demonstrated strong initiative.",
            db
        )
        print("Test 14 (Mastery-level draft):", result)

        # Test 15: draft_assessment — a lower, Not Yet Competent score
        result = await draft_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            35,
            "Aaron needed significant guidance and struggled with the core concept.",
            db
        )
        print("Test 15 (Not Yet Competent draft):", result)

        # Test 16: draft_assessment — score out of range
        result = await draft_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            150,    
            "Should be rejected.",
            db
        )   
        print("Test 16 (Score out of range):", result)

        # Test 17: draft_assessment — empty comments
        result = await draft_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            70,
            "   ",
            db
        )
        print("Test 17 (Empty comments):", result)

        # Test 18: submit_assessment — Aaron's first real assessment for CSC101
        result = await submit_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            85,
            "Aaron completed the task independently and demonstrated strong initiative.",
            db
        )
        print("Test 18 (Submit Aaron's CSC101 assessment):", result)

        # Test 19: submit_assessment — attempting to submit AGAIN for the same unit should fail
        result = await submit_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "33fc6a6d-743c-4314-933f-2445dc0a004b",
            90,
            "Trying to resubmit.",
            db
        )
        print("Test 19 (Duplicate assessment, should fail):", result)

        # Test 20: submit_assessment — invalid UUID format
        result = await submit_assessment("not-a-real-uuid", "also-not-real", 70, "Should fail.", db)
        print("Test 20 (Invalid UUIDs):", result)

        # Test 21: submit_assessment — score out of range
        result = await submit_assessment(
            "3776de48-b964-4cc0-b1e5-73bce58f6b8b",
            "a7be751d-8ff3-4718-8645-96fa0eb31151",  # CSC102, no assessment yet
            120,
            "Should fail on range.",
            db
        )
        print("Test 21 (Score out of range):", result)

        # Test 22: submit_assessment — a real second unit, should succeed and confirm
        # get_pending_units now excludes CSC101 (since it's assessed) but not the others
        result = await get_pending_units("3776de48-b964-4cc0-b1e5-73bce58f6b8b", db)
        print("Test 22 (Pending units after CSC101 assessed, should show 4 remaining):", result)

if __name__ == "__main__":
    asyncio.run(main())
