"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_db_session
from config.logging_config import get_logger
from schemas.user import UserCreate, UserResponse
from services.auth import AuthService
from repositories.user import UserRepository

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Register new user account."""
    auth_service = AuthService(UserRepository(session))
    
    try:
        user, access_token, refresh_token = await auth_service.register_user(user_data)
        
        # Add tokens to response headers
        response = UserResponse.model_validate(user)
        return response
    
    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login")
async def login(
    credentials: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Login with email/username and password."""
    auth_service = AuthService(UserRepository(session))
    
    user = await auth_service.authenticate_user(
        credentials.get("username"),
        credentials.get("password")
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = auth_service.create_access_token(str(user.id))
    refresh_token = auth_service.create_refresh_token(str(user.id))
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@router.post("/refresh")
async def refresh_token(
    token_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Refresh access token."""
    auth_service = AuthService(UserRepository(session))
    
    new_token = await auth_service.refresh_access_token(token_data.get("refresh_token"))
    
    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return {"access_token": new_token, "token_type": "bearer"}
