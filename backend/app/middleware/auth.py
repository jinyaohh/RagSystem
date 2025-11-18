"""
Authentication middleware for JWT token validation.

Provides dependency injection functions for protecting routes.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from app.core.config import settings
from app.models.user import User
from app.services.supabase_service import get_supabase_service, SupabaseService

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase: SupabaseService = Depends(get_supabase_service)
) -> Optional[User]:
    """
    Get current user from JWT token (optional).

    Returns None if no token or invalid token.
    Used for routes that work with or without authentication.

    Args:
        credentials: HTTP Bearer credentials
        supabase: Supabase service

    Returns:
        User or None
    """
    # If auth is disabled, return None
    if not settings.AUTH_ENABLED:
        return None

    # If no credentials provided, return None
    if not credentials:
        return None

    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Extract user ID from token
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            logger.warning("Token missing 'sub' claim")
            return None

        user_id = UUID(user_id_str)

        # Get user from database
        user = await supabase.get_user_by_id(user_id)

        if not user:
            logger.warning(f"User {user_id} not found in database")
            return None

        return user

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        return None

    except ValueError as e:
        logger.warning(f"Invalid user ID format: {e}")
        return None

    except Exception as e:
        logger.error(f"Unexpected error in get_current_user_optional: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: SupabaseService = Depends(get_supabase_service)
) -> User:
    """
    Get current user from JWT token (required).

    Raises HTTPException if no token or invalid token.
    Used for routes that require authentication.

    Args:
        credentials: HTTP Bearer credentials (required)
        supabase: Supabase service

    Returns:
        User

    Raises:
        HTTPException: If authentication fails
    """
    # If auth is disabled, raise error (this endpoint requires auth)
    if not settings.AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Authentication is not enabled on this server"
        )

    # If no credentials provided, raise error
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Extract user ID from token
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = UUID(user_id_str)

        # Get user from database
        user = await supabase.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except ValueError as e:
        logger.warning(f"Invalid user ID format: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )


def require_auth(user: User = Depends(get_current_user)) -> User:
    """
    Dependency that requires authentication.

    This is a convenience function that can be used as a dependency
    to protect routes.

    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"user_id": user.id}

    Args:
        user: Current user (from get_current_user)

    Returns:
        User
    """
    return user


# ============================================================================
# Token Utilities
# ============================================================================

def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload

    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


def extract_user_id_from_token(token: str) -> Optional[UUID]:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        User UUID or None if invalid
    """
    payload = verify_token(token)

    if not payload:
        return None

    try:
        user_id_str = payload.get("sub")
        if user_id_str:
            return UUID(user_id_str)
    except ValueError:
        pass

    return None
