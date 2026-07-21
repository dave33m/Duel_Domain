from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    email: EmailStr
    username: str = Field(max_length=150)
    password: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class SendOTPRequest(BaseModel):
    user_id: UUID
    otp_type: Literal["password_reset"] = "password_reset"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    user_id: UUID
    otp: str = Field(max_length=6)
    new_password: str


class MessageResponse(BaseModel):
    message: str


class SigninResponse(BaseModel):
    token: str
    username: str
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str
    user_id: str


class UserAdminOut(BaseModel):
    id: str
    username: str
    email: str
    player_id: str | None
    rating: int
    wins: int
    losses: int


class UsersListResponse(BaseModel):
    users: list[UserAdminOut]
