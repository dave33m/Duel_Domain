"""One-off script to flag a user as admin, since there's no Django-admin-style UI.

Usage: python -m scripts.make_admin <email>
"""
import asyncio
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.user import User


async def make_admin(email: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"No user found with email {email}")
            return

        user.is_admin = True
        await db.commit()
        print(f"{email} is now an admin")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.make_admin <email>")
        sys.exit(1)

    asyncio.run(make_admin(sys.argv[1]))
