import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    MessageResponse,
    ResetPasswordRequest,
    SendOTPRequest,
    SigninRequest,
    SigninResponse,
    SignupRequest,
    UsersListResponse,
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


@router.post("/send-otp/", response_model=MessageResponse)
@limiter.limit("20/minute")
async def send_otp(request: Request, body: SendOTPRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.send_otp(db, body.user_id, body.otp_type)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/forgot-password/", response_model=ForgotPasswordResponse)
@limiter.limit("20/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.forgot_password(db, body.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset-password/", response_model=MessageResponse)
@limiter.limit("20/minute")
async def reset_password(request: Request, body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AuthService.reset_password(db, body.user_id, body.otp, body.new_password)
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
    try:
        return await AuthService.delete_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
