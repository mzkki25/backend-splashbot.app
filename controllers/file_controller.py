import uuid
import os

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status

from models.file import File
from schemas.chat import FileUploadResponse
from core.config import UPLOAD_DIR
from core.logger import setup_logger

logger = setup_logger(__name__)


class FileController:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def upload(self, db: AsyncSession, file: UploadFile) -> dict:
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename or "file")[1]
        user_dir = os.path.join(UPLOAD_DIR, self.user_id)
        os.makedirs(user_dir, exist_ok=True)

        storage_path = os.path.join(user_dir, f"{file_id}{file_ext}")
        contents = await file.read()

        with open(storage_path, "wb") as f:
            f.write(contents)

        file_url = f"/static/upload/{self.user_id}/{file_id}{file_ext}"

        file_record = File(
            id=uuid.UUID(file_id),
            user_id=uuid.UUID(self.user_id),
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            storage_path=storage_path,
            url=file_url,
        )
        db.add(file_record)
        await db.commit()

        logger.info(f"File uploaded: {file_id} for user {self.user_id}")

        return FileUploadResponse(
            success=True,
            file_id=file_id,
            url=file_url,
        ).model_dump(mode="json", exclude_none=True)
