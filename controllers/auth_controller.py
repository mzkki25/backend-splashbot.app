import uuid
from datetime import datetime, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from models.user import User
from schemas.chat import UserCreate, UserLogin, LoginResponse
from core.config import JWT_EXPIRE_MINUTES
from core.security import hash_password, verify_password, create_access_token
from core.logger import get_logger

logger = get_logger(__name__)


class AuthController:
    @staticmethod
    async def create_user(db: AsyncSession, user: UserCreate) -> str:
        existing = await db.execute(
            select(User).where(or_(User.email == user.email, User.username == user.username))
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email or username already exists")

        new_user = User(
            email=user.email,
            username=user.username,
            password_hash=hash_password(user.password),
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        logger.info(f"User created: {new_user.id}")
        return str(new_user.id)

    @staticmethod
    async def authenticate_user(db: AsyncSession, user: UserLogin) -> dict:
        query_field = User.email if "@" in user.email_or_username else User.username
        result = await db.execute(
            select(User).where(query_field == user.email_or_username)
        )
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not verify_password(user.password, db_user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

        token = create_access_token(data={"sub": str(db_user.id), "uid": str(db_user.id)})
        logger.info(f"User authenticated: {db_user.id}")
        return {
            "user_id": str(db_user.id),
            "token": token,
            "expires_in": JWT_EXPIRE_MINUTES * 60,
        }
