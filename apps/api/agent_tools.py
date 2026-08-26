import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import User, UserRole

async def get_student_profile(student_id: str, db: AsyncSession) -> dict:
    """
    Retrieves a student;s profile: name, email, programme and institution. 
    Used by SupervisorIQ at the start of an assessment conversation to know who is being assessed.

    Args:
        student_id: The UUID (as a string) of the student,
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: A dictionary containing the student's profile information.
                    {"success": True, "full_name": ..., "email": ..., "programme_name": ..., "institution_name": ...}
        On Failure: A dictionary with an error message.
                    {"success": False, "error": "<reason for failure>"}
    """

    # Validate the UUID format before ever touching the database
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        return {"success": False, "error": "Invalid student ID format"}

    # Fetch the user eagerly loading their institution and programme to avoid lazy loading issues in the same query since we know we will need both

    result = await db.execute(
        select(User)
        .options(selectinload(User.institution), selectinload(User.programme))
        .where(User.id == student_uuid, User.role == UserRole.STUDENT)
    )
    student = result.scalar_one_or_none()

    if student is None:
        return {"success": False, "error": "Student not found"}

    return {
        "success": True,
        "full_name": student.full_name,
        "email": student.email,
        "programme_name": student.programme.name if student.programme else None,
        "institution_name": student.institution.name,
    }