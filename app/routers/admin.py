from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy import select
from app.database import async_session
from app.config import settings
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


async def get_admin_from_request(request: Request):
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
        user = result.scalar_one_or_none()
        if user and user.email in settings.admin_emails_list:
            return user
        return None


@router.get("/admin")
async def admin_page(request: Request):
    admin = await get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=302)

    async with async_session() as db:
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "admin.html",
        {"admin": admin, "users": users},
    )


@router.post("/admin/users/{user_id}/activate")
async def activate_user(request: Request, user_id: int):
    admin = await get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=302)

    async with async_session() as db:
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

        await db.commit()

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/deactivate")
async def deactivate_user(request: Request, user_id: int):
    admin = await get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=302)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.status = "inactive"
            remove_key_from_authorized_keys(user.username)

        await db.commit()

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/regenerate-key")
async def regenerate_user_key(request: Request, user_id: int):
    admin = await get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=302)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            keys = generate_ssh_keys(user.username)
            remove_key_from_authorized_keys(user.username)
            add_key_to_authorized_keys(user.username, keys["public_key"])
            await send_private_key_email(user.email, user.username, keys["private_key_path"])

    return RedirectResponse(url="/admin", status_code=302)


@router.post("/admin/users/{user_id}/delete")
async def delete_user(request: Request, user_id: int):
    admin = await get_admin_from_request(request)
    if not admin:
        return RedirectResponse(url="/login", status_code=302)

    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            remove_key_from_authorized_keys(user.username)
            delete_user_keys(user.username)
            await db.delete(user)

        await db.commit()

    return RedirectResponse(url="/admin", status_code=302)
