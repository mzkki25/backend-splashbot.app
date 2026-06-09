import uuid
import os
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status

from models.file import File
from schemas.chat import FileUploadResponse
from core.logger import get_logger
from core.minio import client as minio_client, MINIO_BUCKET

logger = get_logger(__name__)


class FileController:
    def __init__(self, user_id: str):
        self.user_id = user_id

    async def upload(self, db: AsyncSession, file: UploadFile) -> dict:
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename or "file")[1]
        object_name = f"{self.user_id}/{file_id}{file_ext}"

        contents = await file.read()
        content_type = file.content_type or "application/octet-stream"

        minio_client.put_object(
            MINIO_BUCKET,
            object_name,
            BytesIO(contents),
            length=len(contents),
            content_type=content_type,
        )

        file_url = f"/api/files/{self.user_id}/{file_id}{file_ext}"

        file_record = File(
            id=uuid.UUID(file_id),
            user_id=uuid.UUID(self.user_id),
            filename=file.filename or "unnamed",
            content_type=content_type,
            storage_path=object_name,
            url=file_url,
        )
        db.add(file_record)
        await db.commit()

        logger.info(f"File uploaded to MinIO: {object_name}")

        return FileUploadResponse(
            success=True,
            file_id=file_id,
            url=file_url,
        ).model_dump(mode="json", exclude_none=True)
