"""
One off script to create a platform admin account.
Not exposed as an api endpoint, but can be run from the command line to create a platform admin account.

Usage:
    python create_platform_admin.py --email <email> --password <password> --full_name <full_name>
"""

import asyncio
import getpass
from sqlalchemy import select
from database import AsyncSessionLocal
from models import PlatformAdmin
from security import hash_password


async def create_platform_admin():
    email = input("Email: ").strip()
    full_name = input("Full name: ").strip()
    password = getpass.getpass("Password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("Passwords do not match. Aborting.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters. Aborting.")
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            print(f"A platform admin with email '{email}' already exists. Aborting.")
            return

        admin = PlatformAdmin(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

    print(f"\nPlatform admin created: {admin.email} (id: {admin.id})")


if __name__ == "__main__":
    asyncio.run(create_platform_admin())
