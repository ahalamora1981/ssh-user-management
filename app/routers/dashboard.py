from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.ssh_service import generate_ssh_keys, get_user_keys_dir
from app.email_service import send_private_key_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
async def dashboard_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    keys_dir = get_user_keys_dir(user.username)
    has_key = (keys_dir / "id_ed25519").exists()

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "has_key": has_key},
    )


@router.get("/dashboard/key")
async def download_key(
    request: Request,
    user: User = Depends(get_current_user),
):
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
async def regenerate_key(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
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
