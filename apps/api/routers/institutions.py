from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Institution
import secrets
import string
from dependencies import get_current_platform_admin
from models import PlatformAdmin, User, UserRole, InstitutionStatus
from datetime import datetime, timezone
from security import hash_password

router = APIRouter(prefix="/institutions", tags=["institutions"])

class InstitutionRegisterRequest(BaseModel):
    name: str
    tvet_registration_number: str
    contact_person_name: str
    phone_number: str
    email: EmailStr
    county: str
    town: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_institution(
    request: InstitutionRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Check for existing registration number or email before attempting insert
    # gives a clean 409 instead of surfacing a raw IntegrityError to the caller.
    result = await db.execute(
        select(Institution).where(
            (Institution.tvet_registration_number == request.tvet_registration_number)
            | (Institution.email == request.email)
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An institution with this registration number or email already exists",
        )

    institution = Institution(
        name=request.name,
        tvet_registration_number=request.tvet_registration_number,
        contact_person_name=request.contact_person_name,
        phone_number=request.phone_number,
        email=request.email,
        county=request.county,
        town=request.town,
    )
    db.add(institution)
    await db.commit()
    await db.refresh(institution)

    return {
        "id": str(institution.id),
        "name": institution.name,
        "status": institution.status.value,
        "message": "Registration received. You will be notified once your institution is approved.",
    }

def generate_temp_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


@router.get("/pending")
async def list_pending_institutions(
    current_admin: PlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Institution).where(Institution.status == InstitutionStatus.PENDING)
    )
    institutions = result.scalars().all()

    return [
        {
            "id": str(inst.id),
            "name": inst.name,
            "tvet_registration_number": inst.tvet_registration_number,
            "contact_person_name": inst.contact_person_name,
            "email": inst.email,
            "county": inst.county,
            "town": inst.town,
            "created_at": inst.created_at.isoformat(),
        }
        for inst in institutions
    ]


@router.post("/{institution_id}/approve")
async def approve_institution(
    institution_id: str,
    current_admin: PlatformAdmin = Depends(get_current_platform_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Institution).where(Institution.id == institution_id))
    institution = result.scalar_one_or_none()

    if institution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")

    if institution.status != InstitutionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Institution is already {institution.status.value}, not PENDING",
        )

    temp_password = generate_temp_password()

    admin_user = User(
        institution_id=institution.id,
        email=institution.email,
        hashed_password=hash_password(temp_password),
        full_name=institution.contact_person_name,
        role=UserRole.INSTITUTION_ADMIN,
    )
    db.add(admin_user)

    institution.status = InstitutionStatus.APPROVED
    institution.approved_at = datetime.now(timezone.utc)
    institution.approved_by_id = current_admin.id

    await db.commit()
    await db.refresh(institution)
    await db.refresh(admin_user)

    # DEV-ONLY: returning the temp password directly since Resend isn't wired up yet.
    # Once email sending is implemented, this should be removed from the response
    # and sent to institution.email instead.
    return {
        "institution_id": str(institution.id),
        "status": institution.status.value,
        "admin_user_id": str(admin_user.id),
        "admin_email": admin_user.email,
        "temp_password": temp_password,
        "message": "DEV MODE: temp_password shown here only because email sending is not yet configured.",
    }