from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.chat import UserCreate, UserLogin
from controllers.auth_controller import AuthController
from core.database import get_db
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Signup request: username={user.username}, email={user.email}")
    user_id = await AuthController.create_user(db, user)
    return JSONResponse(
        content={"success": True, "user_id": user_id},
        status_code=status.HTTP_201_CREATED,
    )


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login request: {user.email_or_username}")
    auth_data = await AuthController.authenticate_user(db, user)
    return JSONResponse(
        content={
            "success": True,
            "user_id": auth_data["user_id"],
            "token": auth_data["token"],
        },
        status_code=status.HTTP_200_OK,
    )
