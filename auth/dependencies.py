"""FastAPI dependencies that protect routes with a valid JWT."""

from fastapi import Depends, HTTPException, status
from jwt import PyJWTError

from auth.schemas import UserOut
from auth.security import decode_access_token, oauth2_scheme
from db.database import get_user


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> UserOut:
    """Validate the Bearer token and return the authenticated user.

    Places a 401 on any protected endpoint for missing, invalid, or
    expired tokens, and for tokens that belong to a deleted user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        username = decode_access_token(token)
    except PyJWTError:
        raise credentials_exception

    user = get_user(username)
    if user is None:
        raise credentials_exception

    return UserOut(
        username=user["username"],
        is_admin=user["is_admin"],
    )