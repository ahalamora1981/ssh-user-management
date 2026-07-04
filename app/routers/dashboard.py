from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard_page():
    return {"message": "Dashboard - to be implemented"}
