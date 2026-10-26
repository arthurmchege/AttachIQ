from fastapi import APIRouter
from pydantic import BaseModel
from database import get_db
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User
from security import verify_password, create_access_token
from fastapi import HTTPException, status
from dependencies import get_current_user

class LoginRequest(BaseModel):
    email: str
    password: str

router = APIRouter( prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Query the user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    # Check if the user exists and the password is correct
    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid email or password")

    # Build and return the access token
    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role.value,
        "institution_id": str(user.institution_id)
    })

    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value
    }
