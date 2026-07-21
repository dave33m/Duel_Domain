import random
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.otp import OTP
from app.models.user import User


class OTPService:
    @staticmethod
    async def generate_otp(db: AsyncSession, user: User, otp_type: str = "password_reset") -> str:
        code = "".join(str(random.randint(0, 9)) for _ in range(6))
        expires_at = utcnow() + timedelta(minutes=5)

        await db.execute(
            update(OTP)
            .where(OTP.user_id == user.id, OTP.otp_type == otp_type, OTP.is_used == False)  # noqa: E712
            .values(is_used=True)
        )

        db.add(OTP(user_id=user.id, code=code, otp_type=otp_type, expires_at=expires_at))
        await db.commit()

        # TODO: Send OTP via email/SMS
        print(f"OTP for {user.email} ({otp_type}): {code}")

        return code

    @staticmethod
    async def validate_otp(db: AsyncSession, user: User, code: str, otp_type: str = "password_reset") -> bool:
        result = await db.execute(
            select(OTP).where(
                OTP.user_id == user.id,
                OTP.code == code,
                OTP.otp_type == otp_type,
                OTP.is_used == False,  # noqa: E712
                OTP.expires_at > utcnow(),
            )
        )
        otp = result.scalar_one_or_none()
        if otp is None:
            return False

        otp.is_used = True
        await db.commit()
        return True
