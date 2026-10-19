from typing import Annotated

from pydantic import BaseModel, EmailStr, Field

Username = Annotated[str, Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_.-]+$")]
Password = Annotated[str, Field(min_length=8, max_length=72)]


class SignupRequest(BaseModel):
    email: EmailStr
    username: Username
    password: Password


class SigninRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=72)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: Password


class MessageResponse(BaseModel):
    message: str


class SigninResponse(BaseModel):
    token: str
    username: str
    email: str


class UserAdminOut(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    player_id: str | None
    rating: int
    wins: int
    losses: int


class UsersListResponse(BaseModel):
    users: list[UserAdminOut]
