from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from controllers.file_controller import FileController
from core.database import get_db

router = APIRouter()


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    file_controller = FileController(user["uid"])
    result = await file_controller.upload(db, file)
    return JSONResponse(content=result, status_code=201)
