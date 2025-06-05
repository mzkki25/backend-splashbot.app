from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from models.schemas import UserCreate, UserLogin
from services.auth_service import AuthService

router = APIRouter()

@router.post("/signup", response_model=UserCreate)
async def signup(user: UserCreate):
    user_id = AuthService.create_user(user)
    return JSONResponse(
        content={
            "success": True,
            "user_id": user_id
        },
        status_code=status.HTTP_201_CREATED
    )


@router.post("/login", response_model=UserLogin)
async def login(user: UserLogin):
    auth_data = AuthService.authenticate_user(user)
    return JSONResponse(
        content={
            "success": True,
            "user_id": auth_data["user_id"],
            "token": auth_data["token"]
        },
        status_code=status.HTTP_200_OK
    )