"""
Authentication API endpoints.

Handles user signup, login, and session management with Supabase Auth.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.models.user import User, UserCreate
from app.services.supabase_service import get_supabase_service, SupabaseService
from app.middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Request/Response Models
# ============================================================================

class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class SignupRequest(UserCreate):
    """Signup request model (extends UserCreate)."""
    pass


class AuthResponse(BaseModel):
    """Authentication response with token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: User


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class MessageResponse(BaseModel):
    """Simple message response."""
    message: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Register a new user.

    Creates a new user account with Supabase Auth.

    Args:
        request: Signup request with email, password, full_name

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If signup fails or email already exists
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this server"
        )

    if not supabase.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        # Sign up with Supabase Auth
        auth_response = supabase.client.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name
                }
            }
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user. Email may already be registered."
            )

        # Get user data
        user = User(
            id=auth_response.user.id,
            email=auth_response.user.email,
            full_name=request.full_name,
            created_at=auth_response.user.created_at,
            total_documents=0,
            total_queries=0
        )

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in or 3600,
            user=user
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Signup failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Login with email and password.

    Authenticates user and returns JWT tokens.

    Args:
        request: Login request with email and password

    Returns:
        Authentication response with tokens and user data

    Raises:
        HTTPException: If login fails
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this server"
        )

    if not supabase.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        # Login with Supabase Auth
        auth_response = supabase.client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Get user data
        user_data = await supabase.get_user_by_id(auth_response.user.id)

        if not user_data:
            # Create user record if doesn't exist
            user_data = User(
                id=auth_response.user.id,
                email=auth_response.user.email,
                full_name=auth_response.user.user_metadata.get("full_name"),
                created_at=auth_response.user.created_at,
                total_documents=0,
                total_queries=0
            )

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in or 3600,
            user=user_data
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Logout current user.

    Invalidates the current session.

    Args:
        current_user: Current authenticated user

    Returns:
        Success message
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this server"
        )

    if not supabase.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        supabase.client.auth.sign_out()

        return MessageResponse(message="Successfully logged out")

    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(
    request: RefreshRequest,
    supabase: SupabaseService = Depends(get_supabase_service)
):
    """
    Refresh access token.

    Uses refresh token to get a new access token.

    Args:
        request: Refresh token request

    Returns:
        New authentication tokens

    Raises:
        HTTPException: If refresh fails
    """
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this server"
        )

    if not supabase.client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

    try:
        auth_response = supabase.client.auth.refresh_session(request.refresh_token)

        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        # Get user data
        user_data = await supabase.get_user_by_id(auth_response.user.id)

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in or 3600,
            user=user_data
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.

    Returns the authenticated user's profile.

    Args:
        current_user: Current authenticated user

    Returns:
        User profile data
    """
    return current_user
