from minio import Minio
from minio.error import S3Error

from core.config import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET, MINIO_SECURE
from core.logger import get_logger

logger = get_logger(__name__)

client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_SECURE,
)


def ensure_bucket():
    try:
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            logger.info(f"Bucket '{MINIO_BUCKET}' created")
    except S3Error as e:
        logger.error(f"MinIO bucket error: {e}")


ensure_bucket()
