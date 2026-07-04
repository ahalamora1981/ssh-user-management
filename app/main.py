from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from pathlib import Path
from app.database import init_db
from app.config import settings

app = FastAPI(title="SSH User Management")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def index():
    return RedirectResponse(url="/login")


# Import and include routers
from app.routers import pages, dashboard, admin
app.include_router(pages.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
