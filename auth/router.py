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
from auth.schemas import Token, UserOut
from auth.security import create_access_token, verify_password
from db.database import get_user


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


@api_router.get("/me", response_model=UserOut)
async def me(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Return the authenticated user (used on page load to show the name)."""
    return current_user