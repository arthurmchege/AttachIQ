import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import User, UserRole, Placement, CompetencyUnit, Assessment

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

async def get_pending_units(student_id: str, db: AsyncSession) -> dict:
    """
    Returns the competency units belonging to the student's programme that do not
    yet have a submitted assessment recorded against the student's placement.
    Used by SupervisorIQ to know which units still need to be assessed.

    Args:
        student_id: The UUID (as a string) of the student.
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: {"success": True, "pending_units": [{"id": ..., "code": ..., "name": ...}, ...]}
        On Failure: {"success": False, "error": "<reason for failure>"}
    """

    # Validate the UUID format before ever touching the database
    try:
        student_uuid = uuid.UUID(student_id)
    except ValueError:
        return {"success": False, "error": "Invalid student ID format"}

    # Fetch the student, eagerly loading their programme since we need programme_id
    result = await db.execute(
        select(User)
        .options(selectinload(User.programme))
        .where(User.id == student_uuid, User.role == UserRole.STUDENT)
    )
    student = result.scalar_one_or_none()

    if student is None:
        return {"success": False, "error": "Student not found"}

    if student.programme_id is None:
        return {"success": False, "error": "Student has no programme assigned"}

    # Fetch the student's placement — MVP assumption: one active placement per student
    result = await db.execute(
        select(Placement).where(Placement.student_id == student_uuid)
    )
    placement = result.scalars().first()

    if placement is None:
        return {"success": False, "error": "Student has no placement"}

    # All competency units required by the student's programme
    result = await db.execute(
        select(CompetencyUnit).where(CompetencyUnit.programme_id == student.programme_id)
    )
    all_units = result.scalars().all()

    # Unit IDs that already have an assessment recorded for this placement
    result = await db.execute(
        select(Assessment.competency_unit_id).where(Assessment.placement_id == placement.id)
    )
    assessed_unit_ids = {row[0] for row in result.all()}

    pending = [
        {"id": str(unit.id), "code": unit.code, "name": unit.name}
        for unit in all_units
        if unit.id not in assessed_unit_ids
    ]

    return {"success": True, "pending_units": pending}

async def get_competency_detail(unit_id: str, db: AsyncSession) -> dict:
    """
    Retrieves full detail for a single competency unit, including which
    programme it belongs to. Used by SupervisorIQ to explain to the
    supervisor what a competency unit requires before presenting evidence.

    Args:
        unit_id: The UUID (as a string) of the competency unit.
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: {"success": True, "code": ..., "name": ..., "programme_name": ...}
        On Failure: {"success": False, "error": "<reason for failure>"}
    """

    # Validate the UUID format before ever touching the database
    try:
        unit_uuid = uuid.UUID(unit_id)
    except ValueError:
        return {"success": False, "error": "Invalid competency unit ID format"}

    result = await db.execute(
        select(CompetencyUnit)
        .options(selectinload(CompetencyUnit.programme))
        .where(CompetencyUnit.id == unit_uuid)
    )
    unit = result.scalar_one_or_none()

    if unit is None:
        return {"success": False, "error": "Competency unit not found"}

    return {
        "success": True,
        "id": str(unit.id),
        "code": unit.code,
        "name": unit.name,
        "programme_name": unit.programme.name,
    }