from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import require_admin
from app.models import User
from app.ssh_service import (
    generate_ssh_keys,
    add_key_to_authorized_keys,
    remove_key_from_authorized_keys,
    delete_user_keys,
    get_user_keys_dir,
)
from app.email_service import send_private_key_email

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/admin")
async def admin_page(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    return templates.TemplateResponse(
        "admin.html",
        {"request": request, "admin": admin, "users": users},
    )


@router.post("/admin/users/{user_id}/activate")
async def activate_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        user.status = "active"

        # Generate keys if not exists
        keys_dir = get_user_keys_dir(user.username)
        if not (keys_dir / "id_ed25519").exists():
            keys = generate_ssh_keys(user.username)
            add_key_to_authorized_keys(user.username, keys["public_key"])
            await send_private_key_email(user.email, user.username, keys["private_key_path"])

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/deactivate")
async def deactivate_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        user.status = "inactive"
        remove_key_from_authorized_keys(user.username)

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/regenerate-key")
async def regenerate_user_key(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        keys = generate_ssh_keys(user.username)
        remove_key_from_authorized_keys(user.username)
        add_key_to_authorized_keys(user.username, keys["public_key"])
        await send_private_key_email(user.email, user.username, keys["private_key_path"])

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/delete")
async def delete_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        remove_key_from_authorized_keys(user.username)
        delete_user_keys(user.username)
        await db.delete(user)

    return RedirectResponse(url="/admin", status_code=302)
