import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models import User, UserRole, Placement, CompetencyUnit, Assessment, EvidenceSubmission, Assessment

async def get_student_profile(student_id: str, db: AsyncSession) -> dict:
    """
    Retrieves a student's profile: name, email, programme and institution. 
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

async def get_student_evidence(student_id: str, unit_id: str, db: AsyncSession) -> dict:
    """
    Retrieves all evidence submissions a student has made for a specific
    competency unit, via their placement. Used by SupervisorIQ to review
    what the student has actually submitted before asking assessment questions.

    Args:
        student_id: The UUID (as a string) of the student.
        unit_id: The UUID (as a string) of the competency unit.
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: {"success": True, "evidence": [{"file_url": ..., "description": ..., "submitted_at": ...}, ...]}
        On Failure: {"success": False, "error": "<reason for failure>"}
    """

    # Validate both UUID formats before ever touching the database
    try:
        student_uuid = uuid.UUID(student_id)
        unit_uuid = uuid.UUID(unit_id)
    except ValueError:
        return {"success": False, "error": "Invalid student ID or competency unit ID format"}

    # Find the student's placement — MVP assumption: one placement per student
    result = await db.execute(
        select(Placement).where(Placement.student_id == student_uuid)
    )
    placement = result.scalars().first()

    if placement is None:
        return {"success": False, "error": "Student has no placement"}

    # Fetch evidence for that placement + competency unit combination
    result = await db.execute(
        select(EvidenceSubmission).where(
            EvidenceSubmission.placement_id == placement.id,
            EvidenceSubmission.competency_unit_id == unit_uuid,
        )
    )
    submissions = result.scalars().all()

    evidence = [
        {
            "file_url": e.file_url,
            "description": e.description,
            "submitted_at": e.submitted_at.isoformat() if e.submitted_at else None,
        }
        for e in submissions
    ]

    return {"success": True, "evidence": evidence}

def _get_competence_label(score: int) -> str:
    """ Maps a 0-100 score to its CDACC competence band label."""
    if score >= 80:
        return "Mastery"
    elif score >= 65:
        return "Proficient"
    elif score >= 50:
        return "Competent"
    else:
        return "Not Yet Competent" 

async def draft_assessment(student_id: str, unit_id: str, score: int, comments: str, db: AsyncSession) -> dict:
    """
    Packages a supervisor's assessment decision into a draft object for confirmation before it is persisted. Does NOT write to the database, that only happens in submit_assessment, once the supervisor confirms this draft accurately reflects what they observed.

    The score follows the CDACC competence scale:
        80-100: Mastery
        65-79: Proficient
        50-64: Competent
        0-49: Not Yet Competent

    Args:
        student_id: The UUID (as a string) of the student.
        unit_id: The UUID (as a string) of the competency unit.
        score: An integer from 0 to 100 representing the supervisor's assessment score.
        comments: THe supervisor' written comments, informed by the student's submitted evidence and their own observations.
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: {"success": True, "draft": {"student_id": ..., "unit_id": ..., "score": ..., "competence_label": ..., "comments": ...}}
        On Failure: {"success": False, "error": "<reason for failure>"}

    """

    # Validate UUID formats before ever touching the database
    try:
        student_uuid = uuid.UUID(student_id)
        unit_uuid = uuid.UUID(unit_id)
    except ValueError:
        return {"success": False, "error": "Invalid student ID or competency unit ID format"}

    # Validate score is within the CDACC scale
    if not isinstance(score, int) or not (0 <= score <= 100):
        return {"success": False, "error": "Score must be an integer between 0 and 100"}

    if not comments or not comments.strip():
        return {"success": False, "error": "Comments cannot be empty"}

    # Confirm the student and unit actually exist before drafting anything
    student_result = await db.execute(select(User).where(User.id == student_uuid, User.role == UserRole.STUDENT))
    if student_result.scalar_one_or_none() is None:
        return {"success": False, "error": "Student not found"}

    unit_result = await db.execute(select(CompetencyUnit).where(CompetencyUnit.id == unit_uuid))
    if unit_result.scalar_one_or_none() is None:
        return {"success": False, "error": "Competency unit not found"}

    return {
        "success": True,
        "draft": {
            "student_id": student_id,
            "unit_id": unit_id,
            "score": score,
            "competence_label": _get_competence_label(score),
            "comments": comments.strip(),
        },
    }

async def submit_assessment(student_id: str, unit_id: str, score: int, comments: str, db: AsyncSession) -> dict:
    """
    Persists a supervisor's confirmed assessment to the database. This is
    the only SupervisorIQ tool that writes to the database — it should only
    be called after the supervisor has explicitly confirmed the draft
    produced by draft_assessment.

    Refuses to create a duplicate assessment if one already exists for the
    same student's placement and competency unit — an assessment can only
    be submitted once per unit under this MVP's workflow.

    The score follows the CDACC competence scale:
        80-100: Mastery
        65-79:  Proficient
        50-64:  Competent
        0-49:   Not Yet Competent

    Args:
        student_id: The UUID (as a string) of the student.
        unit_id: The UUID (as a string) of the competency unit.
        score: An integer from 0 to 100 representing the supervisor's confirmed assessment.
        comments: The supervisor's confirmed written comments.
        db: An active SQLAlchemy AsyncSession for database access.

    Returns:
        On Success: {"success": True, "assessment": {"id": ..., "student_id": ...,
                     "unit_id": ..., "score": ..., "competence_label": ...,
                     "comments": ..., "assessed_at": ...}}
        On Failure: {"success": False, "error": "<reason for failure>"}
    """

    # Validate UUID formats before ever touching the database
    try:
        student_uuid = uuid.UUID(student_id)
        unit_uuid = uuid.UUID(unit_id)
    except ValueError:
        return {"success": False, "error": "Invalid student ID or competency unit ID format"}

    # Validate score is within the CDACC scale
    if not isinstance(score, int) or not (0 <= score <= 100):
        return {"success": False, "error": "Score must be an integer between 0 and 100"}

    if not comments or not comments.strip():
        return {"success": False, "error": "Comments cannot be empty"}

    # Confirm the student exists and has a placement
    student_result = await db.execute(select(User).where(User.id == student_uuid, User.role == UserRole.STUDENT))
    if student_result.scalar_one_or_none() is None:
        return {"success": False, "error": "Student not found"}

    placement_result = await db.execute(select(Placement).where(Placement.student_id == student_uuid))
    placement = placement_result.scalars().first()
    if placement is None:
        return {"success": False, "error": "Student has no placement"}

    # Confirm the competency unit exists
    unit_result = await db.execute(select(CompetencyUnit).where(CompetencyUnit.id == unit_uuid))
    if unit_result.scalar_one_or_none() is None:
        return {"success": False, "error": "Competency unit not found"}

    # Guard against duplicate assessments for the same placement + unit
    existing_result = await db.execute(
        select(Assessment).where(
            Assessment.placement_id == placement.id,
            Assessment.competency_unit_id == unit_uuid,
        )
    )
    if existing_result.scalar_one_or_none() is not None:
        return {"success": False, "error": "Assessment already submitted for this competency unit"}

    assessment = Assessment(
        placement_id=placement.id,
        competency_unit_id=unit_uuid,
        score=score,
        comments=comments.strip(),
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)

    return {
        "success": True,
        "assessment": {
            "id": str(assessment.id),
            "student_id": student_id,
            "unit_id": unit_id,
            "score": assessment.score,
            "competence_label": _get_competence_label(assessment.score),
            "comments": assessment.comments,
            "assessed_at": assessment.assessed_at.isoformat() if assessment.assessed_at else None,
        },
    }