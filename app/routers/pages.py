import re
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token
from app.email_service import send_verification_email
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

USERNAME_REGEX = re.compile(r'^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$')


def validate_username(username: str) -> bool:
    return bool(USERNAME_REGEX.match(username))


@router.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html")


@router.post("/signup")
async def signup_submit(
    request: Request,
    email: str = "",
    username: str = "",
    password: str = "",
    confirm_password: str = "",
    db: AsyncSession = Depends(get_db),
):
    errors = []

    # Validate email
    if not email or "@" not in email:
        errors.append("Invalid email address")

    # Validate username
    username = username.lower().strip()
    if not validate_username(username):
        errors.append("Username must be 3-32 lowercase alphanumeric characters or hyphens")

    # Validate password
    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
        errors.append("Password must contain both letters and numbers")

    # Check password match
    if password != confirm_password:
        errors.append("Passwords do not match")

    # Check existing user
    if not errors:
        existing = await db.execute(
            select(User).where((User.email == email) | (User.username == username))
        )
        if existing.scalar_one_or_none():
            errors.append("Email or username already exists")

    if errors:
        return templates.TemplateResponse(
            request,
            "signup.html",
            {"errors": errors, "email": email, "username": username},
        )

    # Create user
    token = secrets.token_urlsafe(32)
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        status="pending",
        verification_token=token,
        token_expiry=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(user)
    await db.flush()

    # Send verification email
    await send_verification_email(email, username, token)

    return templates.TemplateResponse(
        request,
        "signup.html",
        {"success": "Account created! Check your email to verify."},
    )


@router.get("/verify/{token}")
async def verify_email(
    request: Request,
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        return templates.TemplateResponse(
            request,
            "verify.html",
            {"error": "Invalid verification link"},
        )

    if user.token_expiry < datetime.utcnow():
        return templates.TemplateResponse(
            request,
            "verify.html",
            {"error": "Verification link has expired"},
        )

    # Activate user
    user.status = "active"
    user.verification_token = None
    user.token_expiry = None

    # Generate SSH keys
    from app.ssh_service import generate_ssh_keys, add_key_to_authorized_keys
    from app.email_service import send_private_key_email

    keys = generate_ssh_keys(user.username)
    add_key_to_authorized_keys(user.username, keys["public_key"])
    await send_private_key_email(user.email, user.username, keys["private_key_path"])

    return templates.TemplateResponse(
        request,
        "verify.html",
        {"success": "Account verified! Your SSH key has been sent to your email."},
    )


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = "",
    password: str = "",
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Invalid email or password"},
        )

    if user.status != "active":
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Account not verified. Check your email."},
        )

    # Create JWT token
    token = create_access_token({"sub": user.id})

    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
