import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.player import Player
from app.models.user import User
from app.services.otp_service import OTPService


class AuthService:
    @staticmethod
    async def signup(db: AsyncSession, email: str, username: str, password: str) -> dict:
        existing_email = await db.execute(select(User).where(User.email == email))
        if existing_email.scalar_one_or_none():
            raise ValueError("Email already exists")

        existing_username = await db.execute(select(User).where(User.username == username))
        if existing_username.scalar_one_or_none():
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
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        token = create_access_token(str(user.id), user.username, user.email)
        return {"token": token, "username": user.username, "email": user.email}

    @staticmethod
    async def send_otp(db: AsyncSession, user_id: uuid.UUID, otp_type: str) -> dict:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("User not found")

        await OTPService.generate_otp(db, user, otp_type)
        return {"message": "OTP sent successfully"}

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> dict:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("Email not found")

        await OTPService.generate_otp(db, user, "password_reset")
        return {"message": "Password reset OTP sent successfully", "user_id": str(user.id)}

    @staticmethod
    async def reset_password(db: AsyncSession, user_id: uuid.UUID, otp: str, new_password: str) -> dict:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("User not found")

        if not await OTPService.validate_otp(db, user, otp, "password_reset"):
            raise ValueError("Invalid or expired OTP")

        validate_password_strength(new_password, username=user.username, email=user.email)

        user.password_hash = hash_password(new_password)
        await db.commit()
        return {"message": "Password reset successful"}

    @staticmethod
    async def get_all_users(db: AsyncSession) -> list[dict]:
        result = await db.execute(select(User).options(selectinload(User.player)))
        users = result.scalars().all()
        return [
            {
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "player_id": str(u.player.id) if u.player else None,
                "rating": u.player.rating if u.player else 1000,
                "wins": u.player.wins if u.player else 0,
                "losses": u.player.losses if u.player else 0,
            }
            for u in users
        ]

    @staticmethod
    async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> dict:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise ValueError("User not found")

        await db.delete(user)
        await db.commit()
        return {"message": "User deleted successfully"}
