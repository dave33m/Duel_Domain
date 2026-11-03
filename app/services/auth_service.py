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
from app.services.email_service import EmailService
from app.services.otp_service import (
    EMAIL_VERIFICATION,
    OTP_TTL_MINUTES,
    PASSWORD_CHANGE,
    PASSWORD_RESET,
    OTPService,
)

RESET_REQUESTED_MESSAGE = "If an account exists for that email, a password reset code has been sent."
VERIFICATION_SENT_MESSAGE = "If that account still needs verifying, a new verification code has been sent."


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

        code = await OTPService.generate_otp(db, user, EMAIL_VERIFICATION)
        EmailService.verification_code(user, code, OTP_TTL_MINUTES[EMAIL_VERIFICATION])
        EmailService.new_signup_alert(user)

        return {"message": "Sign up successful. Check your email for a verification code."}

    @staticmethod
    async def verify_email(db: AsyncSession, email: str, code: str) -> dict:
        user = await get_user_by_email(db, email)
        if user is None or not user.is_active:
            raise ValueError("Invalid or expired code")

        if user.is_email_verified:
            return {"message": "Email already verified"}

        if not await OTPService.validate_otp(db, user, code, EMAIL_VERIFICATION):
            raise ValueError("Invalid or expired code")

        user.is_email_verified = True
        await db.commit()
        EmailService.welcome(user)
        return {"message": "Email verified"}

    @staticmethod
    async def resend_verification(db: AsyncSession, email: str) -> dict:
        # Same response either way, so this can't be used to probe for accounts.
        user = await get_user_by_email(db, email)
        if user is not None and user.is_active and not user.is_email_verified:
            code = await OTPService.generate_otp(db, user, EMAIL_VERIFICATION)
            EmailService.verification_code(user, code, OTP_TTL_MINUTES[EMAIL_VERIFICATION])
        return {"message": VERIFICATION_SENT_MESSAGE}

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
        return {
            "token": token,
            "username": user.username,
            "email": user.email,
            "email_verified": user.is_email_verified,
        }

    @staticmethod
    async def forgot_password(db: AsyncSession, email: str) -> dict:
        # Same response whether or not the account exists, so emails can't be probed.
        user = await get_user_by_email(db, email)
        if user is not None and user.is_active:
            code = await OTPService.generate_otp(db, user, PASSWORD_RESET)
            EmailService.password_reset_code(user, code, OTP_TTL_MINUTES[PASSWORD_RESET])
        return {"message": RESET_REQUESTED_MESSAGE}

    @staticmethod
    async def reset_password(db: AsyncSession, email: str, otp: str, new_password: str) -> dict:
        user = await get_user_by_email(db, email)
        if user is None or not user.is_active:
            # Apply the same password checks first, so the error doesn't reveal whether the account exists.
            validate_password_strength(new_password, email=email)
            raise ValueError("Invalid or expired OTP")

        # Check the new password first, so a rejected password doesn't use up the code.
        validate_password_strength(new_password, username=user.username, email=user.email)

        if not await OTPService.validate_otp(db, user, otp, PASSWORD_RESET):
            raise ValueError("Invalid or expired OTP")

        user.password_hash = hash_password(new_password)
        user.token_version += 1
        # Receiving the code proves they own the inbox.
        user.is_email_verified = True
        await db.commit()
        EmailService.password_changed(user)
        return {"message": "Password reset successful"}

    @staticmethod
    async def request_password_change(db: AsyncSession, user: User, current_password: str) -> dict:
        """Step 1 of changing a password while signed in: check the current one, email a code."""
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        code = await OTPService.generate_otp(db, user, PASSWORD_CHANGE)
        EmailService.password_change_code(user, code, OTP_TTL_MINUTES[PASSWORD_CHANGE])
        return {"message": "A confirmation code has been sent to your email"}

    @staticmethod
    async def confirm_password_change(db: AsyncSession, user: User, code: str, new_password: str) -> dict:
        """Step 2: with the emailed code, set the new password and sign out other sessions."""
        # Check the new password first, so a rejected password doesn't use up the code.
        if verify_password(new_password, user.password_hash):
            raise ValueError("New password must be different from the current one")

        validate_password_strength(new_password, username=user.username, email=user.email)

        if not await OTPService.validate_otp(db, user, code, PASSWORD_CHANGE):
            raise ValueError("Invalid or expired code")

        user.password_hash = hash_password(new_password)
        user.token_version += 1
        await db.commit()
        EmailService.password_changed(user)

        # Old tokens (including the caller's) are now revoked; hand back a fresh one.
        token = create_access_token(str(user.id), user.username, user.email, user.token_version)
        return {"message": "Password changed", "token": token}

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
                "email_verified": u.is_email_verified,
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
