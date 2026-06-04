from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import decode_access_token
from core.database import get_db
from core.logger import get_logger

logger = get_logger(__name__)


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Auth attempt with missing or malformed Bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    token = authorization.split("Bearer ")[1]
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub") or payload.get("uid")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return {"uid": user_id, "sub": user_id}
    except Exception:
        logger.warning("Auth attempt with invalid or expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
