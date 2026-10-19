import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.player import Player
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


async def _user_from_token(token: str, db: AsyncSession) -> User | None:
    """The active user a token belongs to, or None if the token is invalid, revoked or for a disabled account."""
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["user_id"])
        token_version = int(payload.get("ver", 0))
    except (ValueError, KeyError, TypeError):
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active or token_version != user.token_version:
        return None

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided.")

    user = await _user_from_token(credentials.credentials, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user


async def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action.")
    return user


async def get_current_player(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Player:
    result = await db.execute(select(Player).where(Player.user_id == user.id))
    player = result.scalar_one_or_none()
    if player is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Player profile not found")
    return player


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    return await _user_from_token(credentials.credentials, db)
