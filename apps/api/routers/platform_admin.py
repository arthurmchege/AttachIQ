from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import PlatformAdmin
from security import verify_password, create_access_token

router = APIRouter(prefix="/platform-admin", tags=["platform-admin"])


class PlatformAdminLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
async def platform_admin_login(
    request: PlatformAdminLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlatformAdmin).where(PlatformAdmin.email == request.email)
    )
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(request.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token({
        "sub": str(admin.id),
        "role": "PLATFORM_ADMIN",
    })

    return {"access_token": access_token, "token_type": "bearer"}