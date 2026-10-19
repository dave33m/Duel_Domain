import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    normalize_email,
    validate_password_strength,
    verify_password,
)
from app.models.player import Player
from app.models.user import User
from app.services.otp_service import OTPService

RESET_REQUESTED_MESSAGE = "If an account exists for that email, a password reset code has been sent."


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(func.lower(User.email) == normalize_email(email)))
    return result.scalars().first()


async def username_taken(db: AsyncSession, username: str, exclude_user_id: uuid.UUID | None = None) -> bool:
    stmt = select(User.id).where(func.lower(User.username) == username.lower())
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return (await db.execute(stmt)).first() is not None


class AuthService:
    @staticmethod
    async def signup(db: AsyncSession, email: str, username: str, password: str) -> dict:
        email = normalize_email(email)
        if await get_user_by_email(db, email):
            raise ValueError("Email already exists")

        if await username_taken(db, username):
            raise ValueError("Username already exists")

        validate_password_strength(password, username=username, email=email)

        user = User(id=uuid.uuid4(), email=email, username=username, password_hash=hash_password(password))
        db.add(user)
        await db.flush()

        db.add(Player(id=uuid.uuid4(), user_id=user.id))
        await db.commit()

        return {"message": "Sign up successful, welcome to Duel Domain"}

    @staticmethod
    async def signin(db: AsyncSession, email: str, password: str) -> dict:
        user = await get_user_by_email(db, email)
        if user is None:
            verify_password(password, DUMMY_PASSWORD_HASH)
            raise ValueError("Invalid credentials")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("This account has been disabled")

        token = create_access_token(str(user.id), user.username, user.email, user.token_version)
        return {"token": token, "username": user.username, "email": user.email}

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> dict:
        # Same response whether or not the account exists, so emails can't be probed.
        user = await get_user_by_email(db, email)
        if user is not None and user.is_active:
            await OTPService.generate_otp(db, user, "password_reset")
        return {"message": RESET_REQUESTED_MESSAGE}

    @staticmethod
    async def reset_password(db: AsyncSession, email: str, otp: str, new_password: str) -> dict:
        user = await get_user_by_email(db, email)
        if user is None or not user.is_active:
            raise ValueError("Invalid or expired OTP")

        if not await OTPService.validate_otp(db, user, otp, "password_reset"):
            raise ValueError("Invalid or expired OTP")

        validate_password_strength(new_password, username=user.username, email=user.email)

        user.password_hash = hash_password(new_password)
        user.token_version += 1
        await db.commit()
        return {"message": "Password reset successful"}

    @staticmethod
    async def get_all_users(db: AsyncSession) -> list[dict]:
        result = await db.execute(select(User).options(selectinload(User.player)).order_by(User.date_joined))
        users = result.scalars().all()
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "is_active": u.is_active,
                "player_id": str(u.player.id) if u.player else None,
                "rating": u.player.rating if u.player else 1000,
                "wins": u.player.wins if u.player else 0,
                "losses": u.player.losses if u.player else 0,
            }
            for u in users
        ]

    @staticmethod
    async def deactivate_user(db: AsyncSession, user_id: uuid.UUID, acting_admin_id: uuid.UUID) -> dict:
        """Disables the account instead of deleting it, so opponents keep their duel history."""
        if user_id == acting_admin_id:
            raise ValueError("You cannot deactivate your own account")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("User not found")

        user.is_active = False
        await db.commit()
        return {"message": "User deactivated successfully"}
