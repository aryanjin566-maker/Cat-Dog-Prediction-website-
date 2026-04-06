from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from utils.security import security
import logging

logger = logging.getLogger(__name__)

security_scheme = HTTPBearer()

async def get_current_user(credentials = Depends(security_scheme)):
    """
    Dependency to verify JWT token and get current user
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    token = credentials.credentials
    
    payload = security.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload