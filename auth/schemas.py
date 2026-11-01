"""Pydantic schemas for the authentication API."""

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    """Public user information returned to the client."""

    username: str
    is_admin: bool = False


class RegisterRequest(BaseModel):
    """Payload for creating a new account."""

    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[a-zA-Z0-9_.-]+$",
        description="Letters, digits, dots, dashes and underscores only.",
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="At least 8 characters long.",
    )


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserOut