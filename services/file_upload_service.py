import uuid
import os
from typing import Dict, Any

from fastapi import UploadFile, HTTPException, status
from firebase_admin import firestore
from models.schemas import FileUploadResponse

from core.firebase import bucket, db
from core.logging_logger import setup_logger

logger = setup_logger(__name__)


class FileUploadService:
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id

    async def upload_file(self, file: UploadFile) -> Dict[str, Any]:
        try:
            file_id = str(uuid.uuid4())
            file_extension = os.path.splitext(file.filename)[1]
            file_path = f"users/{self.user_id}/{file_id}{file_extension}"

            logger.info(f"Uploading file: {file.filename} for user: {self.user_id}")

            blob = bucket.blob(file_path)
            contents = await file.read()
            blob.upload_from_string(contents, content_type=file.content_type)

            file_url = blob.public_url
            logger.info(f"File uploaded successfully: {file.filename} → {file_url}")

            metadata = {
                'user_id': self.user_id,
                'filename': file.filename,
                'content_type': file.content_type,
                'storage_path': file_path,
                'url': file_url,
                'created_at': firestore.SERVER_TIMESTAMP
            }

            db.collection('files').document(file_id).set(metadata)
            logger.info(f"File metadata saved to Firestore: {file_id}")

            file_upload_response = FileUploadResponse(
                success=True,
                file_id=file_id,
                url=file_url
            )

            logger.info(f"File upload response created: {file_upload_response}")

            return {
                "success": True,
                "file_id": file_id,
                "url": file_url
            }

        except Exception as e:
            logger.error(f"Error uploading file for user {self.user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file. Please try again."
            )
