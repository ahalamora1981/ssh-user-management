from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/signup")
async def signup_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/login")
async def login_page(request: Request):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/verify/{token}")
async def verify_page(request: Request, token: str):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="app/templates")
    return templates.TemplateResponse("verify.html", {"request": request, "token": token})
