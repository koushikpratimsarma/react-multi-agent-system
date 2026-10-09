"""Pydantic schemas for the authentication API."""

from pydantic import BaseModel


class UserOut(BaseModel):
    """Public user information returned to the client."""

    username: str
    is_admin: bool = False


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut