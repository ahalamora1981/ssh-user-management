from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
from jose import JWTError, jwt
from sqlalchemy import select
from app.database import async_session
from app.config import settings
from app.models import User
from app.ssh_service import generate_ssh_keys, get_user_keys_dir
from app.email_service import send_private_key_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def get_user_from_request(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


@router.get("/dashboard")
async def dashboard_page(request: Request):
    user = await get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    keys_dir = get_user_keys_dir(user.username)
    has_key = (keys_dir / "id_ed25519").exists()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "has_key": has_key},
    )


@router.get("/dashboard/key")
async def download_key(request: Request):
    user = await get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    keys_dir = get_user_keys_dir(user.username)
    private_key_path = keys_dir / "id_ed25519"

    if not private_key_path.exists():
        return RedirectResponse(url="/dashboard", status_code=302)

    return FileResponse(
        path=str(private_key_path),
        filename=f"{user.username}_id_ed25519",
        media_type="application/octet-stream",
    )


@router.post("/dashboard/key/regenerate")
async def regenerate_key(request: Request):
    user = await get_user_from_request(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Generate new keys
    keys = generate_ssh_keys(user.username)

    # Update authorized_keys
    from app.ssh_service import remove_key_from_authorized_keys, add_key_to_authorized_keys
    remove_key_from_authorized_keys(user.username)
    add_key_to_authorized_keys(user.username, keys["public_key"])

    # Send new key via email
    await send_private_key_email(user.email, user.username, keys["private_key_path"])

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "has_key": True,
            "success": "New SSH key generated and sent to your email!",
        },
    )
