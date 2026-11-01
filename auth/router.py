"""Authentication routes: JWT API + the login page.

The login page is a thin client-side form: it POSTs the credentials to
/api/auth/login, stores the returned JWT in localStorage, and redirects
to the chat UI. Protected endpoints read the token from the
Authorization header via auth.dependencies.get_current_user.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

from auth.dependencies import get_current_user
from auth.schemas import RegisterRequest, Token, UserOut
from auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from db.database import create_user, get_user


templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------
# Pages
# ---------------------------------------------------------

page_router = APIRouter(include_in_schema=False)


@page_router.get("/login")
async def login_page(request: Request):
    """Serve the login form. Auth state is handled client-side with JWT."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={},
    )


@page_router.get("/logout")
async def logout(request: Request):
    """Redirect target for the logout link (the token is cleared client-side)."""
    return RedirectResponse(url="/login", status_code=303)


# ---------------------------------------------------------
# JWT API
# ---------------------------------------------------------

api_router = APIRouter(prefix="/api/auth", tags=["auth"])


@api_router.post("/login", response_model=Token)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Exchange a username/password for a JWT access token."""
    user = get_user(form.username)

    if user is None or not verify_password(form.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(subject=user["username"])

    return Token(
        access_token=access_token,
        user=UserOut(
            username=user["username"],
            is_admin=user["is_admin"],
        ),
    )


@api_router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
) -> Token:
    """Create a new account and return a JWT so the user is signed in immediately.

    Returns ``409 Conflict`` when the username is already taken.
    """
    username = payload.username.strip()

    created = create_user(username, hash_password(payload.password))

    if not created:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken",
        )

    access_token = create_access_token(subject=username)

    return Token(
        access_token=access_token,
        user=UserOut(username=username, is_admin=False),
    )


@api_router.get("/me", response_model=UserOut)
async def me(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Return the authenticated user (used on page load to show the name)."""
    return current_user