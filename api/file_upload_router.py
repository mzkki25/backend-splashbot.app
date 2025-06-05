from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any

from api.deps import get_current_user
from services.file_upload_service import FileUploadService

router = APIRouter()


@router.post("", response_model=Dict[str, Any])
async def upload_file(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user)
) -> JSONResponse:
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    
    user_id: str = user['uid']
    file_service = FileUploadService(user_id)

    result: Dict[str, Any] = await file_service.upload_file(file)

    return JSONResponse(content=result, status_code=201)
