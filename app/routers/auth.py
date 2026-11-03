import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin, get_current_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ConfirmPasswordChangeRequest,
    ForgotPasswordRequest,
    MessageResponse,
    PasswordChangedResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    SigninRequest,
    SigninResponse,
    SignupRequest,
    UsersListResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def signup(request: Request, body: SignupRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.signup(db, body.email, body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/signin/", response_model=SigninResponse)
@limiter.limit("20/minute")
async def signin(request: Request, body: SigninRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.signin(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/verify-email/", response_model=MessageResponse)
@limiter.limit("10/minute")
async def verify_email(request: Request, body: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.verify_email(db, body.email, body.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resend-verification/", response_model=MessageResponse)
@limiter.limit("3/minute")
async def resend_verification(request: Request, body: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.resend_verification(db, body.email)


@router.post("/change-password/request/", response_model=MessageResponse)
@limiter.limit("5/minute")
async def request_password_change(
    request: Request,
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Checks the current password and emails a confirmation code."""
    try:
        return await AuthService.request_password_change(db, user, body.current_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password/confirm/", response_model=PasswordChangedResponse)
@limiter.limit("10/minute")
async def confirm_password_change(
    request: Request,
    body: ConfirmPasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Sets the new password; all other sessions are signed out and a fresh token is returned."""
    try:
        return await AuthService.confirm_password_change(db, user, body.code, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password/", response_model=MessageResponse)
@limiter.limit("5/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.forgot_password(db, body.email)


@router.post("/reset-password/", response_model=MessageResponse)
@limiter.limit("10/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.reset_password(db, body.email, body.otp, body.new_password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/users/", response_model=UsersListResponse)
async def get_all_users(db: AsyncSession = Depends(get_db), admin: User = Depends(get_current_admin)):
    users = await AuthService.get_all_users(db)
    return {"users": users}


@router.delete("/user/{user_id}/", response_model=MessageResponse)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Deactivates the account; duel history is kept for the other players."""
    try:
        return await AuthService.deactivate_user(db, user_id, admin.id)
    except ValueError as e:
        code = status.HTTP_404_NOT_FOUND if str(e) == "User not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=str(e))
