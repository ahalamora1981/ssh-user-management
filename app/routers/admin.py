from fastapi import APIRouter

router = APIRouter()


@router.get("/admin")
async def admin_page():
    return {"message": "Admin - to be implemented"}
