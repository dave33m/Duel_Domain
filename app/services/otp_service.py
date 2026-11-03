import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.otp import OTP
from app.models.user import User

EMAIL_VERIFICATION = "email_verification"
PASSWORD_RESET = "password_reset"
PASSWORD_CHANGE = "password_change"

# How long each kind of code stays valid.
OTP_TTL_MINUTES = {EMAIL_VERIFICATION: 60, PASSWORD_RESET: 10, PASSWORD_CHANGE: 10}
MAX_ATTEMPTS = 5


class OTPService:
    @staticmethod
    async def generate_otp(db: AsyncSession, user: User, otp_type: str) -> str:
        """Issues a fresh code (replacing any live one of the same type); the caller emails it."""
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = utcnow() + timedelta(minutes=OTP_TTL_MINUTES[otp_type])

        await db.execute(
            update(OTP)
            .where(OTP.user_id == user.id, OTP.otp_type == otp_type, OTP.is_used == False)  # noqa: E712
            .values(is_used=True)
        )

        db.add(OTP(user_id=user.id, code=code, otp_type=otp_type, expires_at=expires_at))
        await db.commit()
        return code

    @staticmethod
    async def validate_otp(db: AsyncSession, user: User, code: str, otp_type: str) -> bool:
        """Checks the user's single live code; too many wrong guesses burn it."""
        result = await db.execute(
            select(OTP).where(
                OTP.user_id == user.id,
                OTP.otp_type == otp_type,
                OTP.is_used == False,  # noqa: E712
                OTP.expires_at > utcnow(),
            )
        )
        otp = result.scalars().first()
        if otp is None:
            return False

        if not hmac.compare_digest(otp.code, code):
            otp.attempts += 1
            if otp.attempts >= MAX_ATTEMPTS:
                otp.is_used = True
            await db.commit()
            return False

        otp.is_used = True
        await db.commit()
        return True
