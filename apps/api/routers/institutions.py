from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Institution

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