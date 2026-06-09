from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from minio.error import S3Error

from core.minio import client as minio_client, MINIO_BUCKET

router = APIRouter(tags=["Files"])


@router.get("/{user_id}/{filename:path}")
async def get_file(user_id: str, filename: str):
    object_name = f"{user_id}/{filename}"
    try:
        response = minio_client.get_object(MINIO_BUCKET, object_name)
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type=response.headers.get("Content-Type", "application/octet-stream"),
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "Cache-Control": "public, max-age=86400",
            },
        )
    except S3Error:
        raise HTTPException(status_code=404, detail="File not found")
