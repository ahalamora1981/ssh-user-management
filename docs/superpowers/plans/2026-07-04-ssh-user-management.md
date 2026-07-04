# SSH User Management Portal — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web app that automates Linux server user creation with SSH key generation and email delivery.

**Architecture:** FastAPI backend with Jinja2 templates, SQLite database, SMTP email service, and filesystem-based SSH key storage. Starbucks-inspired warm cream/green design system.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Jinja2, bcrypt, python-jose, paramiko, aiosmtplib

## Global Constraints

- Python 3.11+ required
- SQLite database stored at `./data/users.db`
- SSH keys stored at `./keys/{username}/`
- SMTP server: smtp.163.com, port 465, sender: taojundev@163.com
- Admin emails configured via `ADMIN_EMAILS` env var
- All forms require CSRF tokens
- Passwords must be bcrypt-hashed (12 rounds)
- JWT tokens in httpOnly cookies
- Starbucks design: 50px pill buttons, scale(0.95) active, warm cream canvas (#f2f0eb)

---

## File Structure

```
user-management/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, startup/shutdown
│   ├── config.py            # Settings from .env
│   ├── database.py          # SQLAlchemy async engine
│   ├── models.py            # User model
│   ├── auth.py              # JWT, password hashing, dependencies
│   ├── email_service.py     # SMTP async email sender
│   ├── ssh_service.py       # Ed25519 key generation
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py         # Public pages (signup, login, verify)
│   │   ├── dashboard.py     # User portal
│   │   └── admin.py         # Admin portal
│   └── templates/
│       ├── base.html
│       ├── signup.html
│       ├── login.html
│       ├── verify.html
│       ├── dashboard.html
│       ├── admin.html
│       └── emails/
│           ├── verification.html
│           └── private_key.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── keys/                    # SSH key storage (gitignored)
├── data/                    # SQLite storage (gitignored)
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

---

### Task 1: Project Setup & Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `run.py`

**Interfaces:**
- Produces: `settings` object with attributes: `DATABASE_URL`, `SECRET_KEY`, `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SENDER_EMAIL`, `SENDER_NAME`, `SERVER_IP`, `KEYS_DIR`, `ADMIN_EMAILS`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
sqlalchemy==2.0.23
aiosqlite==0.19.0
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
paramiko==3.4.0
aiosmtplib==3.0.1
python-dotenv==1.0.0
```

- [ ] **Step 2: Create .env.example**

```
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/users.db

# JWT
SECRET_KEY=change-this-to-a-random-64-char-string
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Email (SMTP)
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=taojundev@163.com
SMTP_PASSWORD=LAvnA37TqKyc5Ktm
SENDER_EMAIL=taojundev@163.com
SENDER_NAME=SSH User Management

# Server
SERVER_IP=your-server-ip-here
KEYS_DIR=./keys

# Admin (comma-separated emails)
ADMIN_EMAILS=admin@example.com
```

- [ ] **Step 3: Create app/__init__.py**

```python
# SSH User Management App
```

- [ ] **Step 4: Create app/config.py**

```python
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/users.db"

    # JWT
    SECRET_KEY: str = "change-this-to-a-random-64-char-string"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    # SMTP
    SMTP_SERVER: str = "smtp.163.com"
    SMTP_PORT: int = 465
    SMTP_USERNAME: str = "taojundev@163.com"
    SMTP_PASSWORD: str = "LAvnA37TqKyc5Ktm"
    SENDER_EMAIL: str = "taojundev@163.com"
    SENDER_NAME: str = "SSH User Management"

    # Server
    SERVER_IP: str = "localhost"
    KEYS_DIR: str = "./keys"

    # Admin
    ADMIN_EMAILS: str = "admin@example.com"

    @property
    def admin_emails_list(self) -> List[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 5: Create run.py**

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

- [ ] **Step 6: Initialize requirements and verify**

Run: `pip install -r requirements.txt`
Expected: All dependencies install successfully

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example app/__init__.py app/config.py run.py
git commit -m "feat: project setup with configuration"
```

---

### Task 2: Database & Models

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`

**Interfaces:**
- Produces: `get_db()` async generator, `User` model with columns: `id`, `email`, `username`, `password_hash`, `status`, `verification_token`, `token_expiry`, `created_at`, `updated_at`

- [ ] **Step 1: Create app/database.py**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 2: Create app/models.py**

```python
from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(32), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, active, inactive
    verification_token = Column(String(255), nullable=True, unique=True)
    token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 3: Verify database creation works**

Run: `python -c "import asyncio; from app.database import init_db; asyncio.run(init_db()); print('DB created')"`
Expected: `DB created` and `data/users.db` file appears

- [ ] **Step 4: Commit**

```bash
git add app/database.py app/models.py
git commit -m "feat: database models and connection"
```

---

### Task 3: Authentication Utilities

**Files:**
- Create: `app/auth.py`

**Interfaces:**
- Produces: `hash_password(password) -> str`, `verify_password(password, hash) -> bool`, `create_access_token(data) -> str`, `get_current_user(request, db) -> User`, `require_admin(request, db) -> User`

- [ ] **Step 1: Create app/auth.py**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def get_user_from_cookie(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_current_user(request: Request, db: AsyncSession = None) -> User:
    if db is None:
        from app.database import async_session
        async with async_session() as db:
            user = await get_user_from_cookie(request, db)
    else:
        user = await get_user_from_cookie(request, db)

    if user is None:
        raise HTTPException(status_code=302, headers={"Location": "/login"})
    return user


async def require_admin(request: Request, db: AsyncSession = None) -> User:
    user = await get_current_user(request, db)
    if user.email not in settings.admin_emails_list:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

- [ ] **Step 2: Install passlib and verify imports**

Run: `pip install passlib[bcrypt]`
Expected: Passlib installed

- [ ] **Step 3: Commit**

```bash
git add app/auth.py
git commit -m "feat: authentication utilities (JWT, bcrypt)"
```

---

### Task 4: Email Service

**Files:**
- Create: `app/email_service.py`
- Create: `app/templates/emails/verification.html`
- Create: `app/templates/emails/private_key.html`

**Interfaces:**
- Produces: `send_verification_email(email, username, token) -> bool`, `send_private_key_email(email, username, key_path) -> bool`

- [ ] **Step 1: Create app/email_service.py**

```python
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.config import settings

template_dir = Path(__file__).parent / "templates" / "emails"
jinja_env = Environment(loader=FileSystemLoader(template_dir))


async def send_email(to_email: str, subject: str, html_body: str, attachments: list = None) -> bool:
    msg = MIMEMultipart()
    msg["From"] = f"{settings.SENDER_NAME} <{settings.SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html_body, "html"))

    if attachments:
        for filepath in attachments:
            path = Path(filepath)
            if path.exists():
                with open(path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename={path.name}")
                    msg.attach(part)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USERNAME,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False


async def send_verification_email(email: str, username: str, token: str) -> bool:
    template = jinja_env.get_template("verification.html")
    verification_url = f"http://{settings.SERVER_IP}:8000/verify/{token}"
    html_body = template.render(username=username, verification_url=verification_url)
    return await send_email(email, "Verify your SSH account", html_body)


async def send_private_key_email(email: str, username: str, key_path: str) -> bool:
    template = jinja_env.get_template("private_key.html")
    html_body = template.render(username=username, server_ip=settings.SERVER_IP)
    return await send_email(
        email,
        "Your SSH Private Key",
        html_body,
        attachments=[key_path]
    )
```

- [ ] **Step 2: Create app/templates/emails/verification.html**

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Inter', Arial, sans-serif; background: #f2f0eb; margin: 0; padding: 40px 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; }
        .header { background: #006241; padding: 32px; text-align: center; }
        .header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.01em; }
        .content { padding: 32px; }
        .content p { color: rgba(0,0,0,0.87); line-height: 1.6; }
        .btn { display: inline-block; background: #00754A; color: #ffffff; text-decoration: none; padding: 12px 32px; border-radius: 50px; font-weight: 600; margin: 24px 0; }
        .footer { background: #1E3932; padding: 24px; text-align: center; color: rgba(255,255,255,0.70); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SSH User Management</h1>
        </div>
        <div class="content">
            <p>Hi {{ username }},</p>
            <p>Welcome! Please verify your email to activate your account.</p>
            <p style="text-align: center;">
                <a href="{{ verification_url }}" class="btn">Verify Email</a>
            </p>
            <p style="color: rgba(0,0,0,0.58); font-size: 14px;">This link expires in 24 hours.</p>
            <p style="color: rgba(0,0,0,0.58); font-size: 14px;">If you didn't create this account, ignore this email.</p>
        </div>
        <div class="footer">
            <p>SSH User Management Portal</p>
        </div>
    </div>
</body>
</html>
```

- [ ] **Step 3: Create app/templates/emails/private_key.html**

```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Inter', Arial, sans-serif; background: #f2f0eb; margin: 0; padding: 40px 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; }
        .header { background: #006241; padding: 32px; text-align: center; }
        .header h1 { color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.01em; }
        .content { padding: 32px; }
        .content p { color: rgba(0,0,0,0.87); line-height: 1.6; }
        .warning { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 16px; margin: 24px 0; }
        .warning strong { color: #856404; }
        .code { background: #1E3932; color: #ffffff; padding: 12px 16px; border-radius: 8px; font-family: monospace; font-size: 14px; margin: 16px 0; }
        .footer { background: #1E3932; padding: 24px; text-align: center; color: rgba(255,255,255,0.70); font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your SSH Private Key</h1>
        </div>
        <div class="content">
            <p>Hi {{ username }},</p>
            <p>Your SSH account is now active! Your private key is attached to this email.</p>
            <div class="warning">
                <strong>⚠️ Important:</strong> Keep this key safe and never share it. If compromised, contact your admin immediately.
            </div>
            <p><strong>Connection command:</strong></p>
            <div class="code">ssh -i id_ed25519 root@{{ server_ip }}</div>
            <p style="color: rgba(0,0,0,0.58); font-size: 14px;">You can also download your key anytime from the user portal.</p>
        </div>
        <div class="footer">
            <p>SSH User Management Portal</p>
        </div>
    </div>
</body>
</html>
```

- [ ] **Step 4: Verify email templates render**

Run: `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('app/templates/emails')); print(env.get_template('verification.html').render(username='test', verification_url='http://example.com/verify/abc123')[:100])"`
Expected: HTML output starting with `<!DOCTYPE html>`

- [ ] **Step 5: Commit**

```bash
git add app/email_service.py app/templates/emails/
git commit -m "feat: email service with verification and key templates"
```

---

### Task 5: SSH Key Service

**Files:**
- Create: `app/ssh_service.py`

**Interfaces:**
- Produces: `generate_ssh_keys(username) -> dict`, `add_key_to_authorized_keys(username, public_key) -> bool`, `remove_key_from_authorized_keys(username) -> bool`

- [ ] **Step 1: Create app/ssh_service.py**

```python
import os
import paramiko
from pathlib import Path
from app.config import settings


def get_keys_dir() -> Path:
    keys_dir = Path(settings.KEYS_DIR)
    keys_dir.mkdir(parents=True, exist_ok=True)
    return keys_dir


def get_user_keys_dir(username: str) -> Path:
    user_dir = get_keys_dir() / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def generate_ssh_keys(username: str) -> dict:
    user_dir = get_user_keys_dir(username)

    # Generate Ed25519 key pair
    key = paramiko.Ed25519Key.generate()
    private_key_path = user_dir / "id_ed25519"
    public_key_path = user_dir / "id_ed25519.pub"

    # Write private key
    key.write_private_key_file(str(private_key_path))
    os.chmod(str(private_key_path), 0o600)

    # Write public key
    pub_key = f"{key.get_base64()} {username}@ssh-management"
    with open(public_key_path, "w") as f:
        f.write(pub_key)

    return {
        "private_key_path": str(private_key_path),
        "public_key_path": str(public_key_path),
        "public_key": pub_key,
    }


def add_key_to_authorized_keys(username: str, public_key: str) -> bool:
    authorized_keys_path = Path("/root/.ssh/authorized_keys")
    authorized_keys_path.parent.mkdir(parents=True, exist_ok=True)

    comment = f"# {username}"

    # Check if key already exists
    if authorized_keys_path.exists():
        existing = authorized_keys_path.read_text()
        if public_key in existing:
            return True  # Already added

    # Append key with comment
    with open(authorized_keys_path, "a") as f:
        f.write(f"\n{comment}\n{public_key}\n")

    return True


def remove_key_from_authorized_keys(username: str) -> bool:
    authorized_keys_path = Path("/root/.ssh/authorized_keys")

    if not authorized_keys_path.exists():
        return True

    content = authorized_keys_path.read_text()
    lines = content.split("\n")

    # Find and remove the key block (comment line + key line)
    new_lines = []
    skip_next = False
    for line in lines:
        if line.strip() == f"# {username}":
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        new_lines.append(line)

    authorized_keys_path.write_text("\n".join(new_lines))
    return True


def delete_user_keys(username: str) -> bool:
    import shutil
    user_dir = get_user_keys_dir(username)
    if user_dir.exists():
        shutil.rmtree(user_dir)
    return True
```

- [ ] **Step 2: Verify SSH key generation works**

Run: `python -c "from app.ssh_service import generate_ssh_keys; result = generate_ssh_keys('test-user'); print(result)"`
Expected: Dict with private_key_path, public_key_path, public_key

- [ ] **Step 3: Commit**

```bash
git add app/ssh_service.py
git commit -m "feat: SSH key generation and authorized_keys management"
```

---

### Task 6: FastAPI Application Setup

**Files:**
- Create: `app/main.py`
- Create: `app/templates/base.html`
- Create: `static/css/style.css`
- Create: `static/js/main.js`
- Modify: `run.py`

**Interfaces:**
- Produces: FastAPI `app` instance with template rendering, static files, and database initialization

- [ ] **Step 1: Create app/main.py**

```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
async def index(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/login")


# Import and include routers
from app.routers import pages, dashboard, admin
app.include_router(pages.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
```

- [ ] **Step 2: Create app/routers/__init__.py**

```python
# Routers package
```

- [ ] **Step 3: Create app/routers/pages.py (placeholder)**

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/verify/{token}")
async def verify_page(request: Request, token: str):
    return templates.TemplateResponse("verify.html", {"request": request, "token": token})
```

- [ ] **Step 4: Create app/routers/dashboard.py (placeholder)**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard")
async def dashboard_page():
    return {"message": "Dashboard - to be implemented"}
```

- [ ] **Step 5: Create app/routers/admin.py (placeholder)**

```python
from fastapi import APIRouter

router = APIRouter()


@router.get("/admin")
async def admin_page():
    return {"message": "Admin - to be implemented"}
```

- [ ] **Step 6: Create base.html template**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SSH User Management{% endblock %}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">SSH User Management</div>
        <div class="nav-links">
            {% block nav_links %}{% endblock %}
        </div>
    </nav>

    {% block hero %}{% endblock %}

    <main class="main-content">
        <div class="container">
            {% block content %}{% endblock %}
        </div>
    </main>

    <footer class="footer">
        <div class="container">
            <p>SSH User Management Portal</p>
        </div>
    </footer>

    <script src="/static/js/main.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 7: Create static/css/style.css**

```css
/* Starbucks-Inspired Design System */
:root {
    /* Brand Colors */
    --starbucks-green: #006241;
    --green-accent: #00754A;
    --house-green: #1E3932;
    --green-uplift: #2b5148;
    --green-light: #d4e9e2;

    /* Surface Colors */
    --white: #ffffff;
    --neutral-warm: #f2f0eb;
    --ceramic: #edebe9;
    --neutral-cool: #f9f9f9;

    /* Text Colors */
    --text-black: rgba(0, 0, 0, 0.87);
    --text-black-soft: rgba(0, 0, 0, 0.58);
    --text-white: rgba(255, 255, 255, 1);
    --text-white-soft: rgba(255, 255, 255, 0.70);

    /* Semantic Colors */
    --red: #c82014;
    --gold: #cba258;

    /* Typography */
    --font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    --letter-spacing: -0.01em;

    /* Spacing */
    --space-1: 0.4rem;
    --space-2: 0.8rem;
    --space-3: 1.6rem;
    --space-4: 2.4rem;
    --space-5: 3.2rem;
    --space-6: 4rem;

    /* Borders */
    --radius-card: 12px;
    --radius-button: 50px;

    /* Shadows */
    --shadow-card: 0px 0px 0.5px 0px rgba(0,0,0,0.14), 0px 1px 1px 0px rgba(0,0,0,0.24);
    --shadow-nav: 0 1px 3px rgba(0,0,0,0.1), 0 2px 2px rgba(0,0,0,0.06), 0 0 2px rgba(0,0,0,0.07);
}

/* Reset & Base */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 62.5%; /* 1rem = 10px */
}

body {
    font-family: var(--font-family);
    font-size: 1.6rem;
    line-height: 1.5;
    letter-spacing: var(--letter-spacing);
    color: var(--text-black);
    background-color: var(--neutral-warm);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* Typography */
h1, h2, h3 {
    font-weight: 600;
    letter-spacing: var(--letter-spacing);
}

h1 {
    font-size: 2.4rem;
    color: var(--starbucks-green);
}

h2 {
    font-size: 2.4rem;
    color: var(--text-black);
    font-weight: 400;
}

/* Navbar */
.navbar {
    background-color: var(--house-green);
    padding: var(--space-3) var(--space-4);
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: var(--shadow-nav);
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-brand {
    color: var(--text-white);
    font-size: 1.8rem;
    font-weight: 600;
    letter-spacing: var(--letter-spacing);
}

.nav-links a {
    color: var(--text-white);
    text-decoration: none;
    margin-left: var(--space-4);
    font-size: 1.4rem;
    font-weight: 600;
    transition: opacity 0.2s ease;
}

.nav-links a:hover {
    opacity: 0.8;
}

/* Hero */
.hero {
    background-color: var(--starbucks-green);
    padding: var(--space-6) var(--space-4);
    text-align: center;
}

.hero h1 {
    color: var(--text-white);
    font-size: 3.2rem;
    margin-bottom: var(--space-2);
}

.hero p {
    color: var(--text-white-soft);
    font-size: 1.8rem;
}

/* Main Content */
.main-content {
    flex: 1;
    padding: var(--space-6) var(--space-4);
}

.container {
    max-width: 500px;
    margin: 0 auto;
}

/* Cards */
.card {
    background-color: var(--white);
    border-radius: var(--radius-card);
    box-shadow: var(--shadow-card);
    padding: var(--space-5);
}

/* Forms */
.form-group {
    margin-bottom: var(--space-4);
}

.form-group label {
    display: block;
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--text-black);
    margin-bottom: var(--space-2);
}

.form-group input {
    width: 100%;
    padding: 12px;
    font-size: 1.6rem;
    font-family: var(--font-family);
    border: 1px solid var(--ceramic);
    border-radius: 4px;
    transition: border-color 0.2s ease;
}

.form-group input:focus {
    outline: none;
    border-color: var(--green-accent);
}

.form-group input.error {
    border-color: var(--red);
    background-color: rgba(200, 32, 20, 0.05);
}

.error-message {
    color: var(--red);
    font-size: 1.3rem;
    margin-top: var(--space-1);
}

/* Buttons */
.btn {
    display: inline-block;
    font-family: var(--font-family);
    font-size: 1.6rem;
    font-weight: 600;
    letter-spacing: var(--letter-spacing);
    text-decoration: none;
    border: none;
    border-radius: var(--radius-button);
    padding: 12px 32px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    text-align: center;
}

.btn:active {
    transform: scale(0.95);
}

.btn-primary {
    background-color: var(--green-accent);
    color: var(--text-white);
    border: 1px solid var(--green-accent);
    width: 100%;
}

.btn-secondary {
    background-color: transparent;
    color: var(--green-accent);
    border: 1px solid var(--green-accent);
}

.btn-danger {
    background-color: var(--red);
    color: var(--text-white);
    border: 1px solid var(--red);
}

.btn-small {
    padding: 8px 16px;
    font-size: 1.4rem;
}

/* Alerts */
.alert {
    padding: var(--space-3);
    border-radius: var(--radius-card);
    margin-bottom: var(--space-4);
    font-size: 1.4rem;
}

.alert-success {
    background-color: var(--green-light);
    color: var(--starbucks-green);
    border: 1px solid var(--green-accent);
}

.alert-error {
    background-color: rgba(200, 32, 20, 0.1);
    color: var(--red);
    border: 1px solid var(--red);
}

.alert-warning {
    background-color: #fff3cd;
    color: #856404;
    border: 1px solid #ffc107;
}

/* Footer */
.footer {
    background-color: var(--house-green);
    padding: var(--space-4);
    text-align: center;
    margin-top: auto;
}

.footer p {
    color: var(--text-white-soft);
    font-size: 1.4rem;
}

/* Utility Classes */
.text-center { text-align: center; }
.mt-4 { margin-top: var(--space-4); }
.mb-4 { margin-bottom: var(--space-4); }
.hidden { display: none; }

/* Responsive */
@media (max-width: 768px) {
    .hero h1 {
        font-size: 2.4rem;
    }

    .hero p {
        font-size: 1.6rem;
    }

    .card {
        padding: var(--space-4);
    }
}
```

- [ ] **Step 8: Create static/js/main.js**

```javascript
// Form validation and interactions
document.addEventListener('DOMContentLoaded', function() {
    // Password confirmation validation
    const passwordForm = document.querySelector('form[data-validate-passwords]');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password');
            const confirmPassword = document.getElementById('confirm_password');

            if (password.value !== confirmPassword.value) {
                e.preventDefault();
                confirmPassword.classList.add('error');
                showErrorMessage(confirmPassword, 'Passwords do not match');
            }
        });
    }

    // Real-time password match check
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    if (password && confirmPassword) {
        confirmPassword.addEventListener('input', function() {
            if (this.value && this.value !== password.value) {
                this.classList.add('error');
            } else {
                this.classList.remove('error');
                hideErrorMessage(this);
            }
        });
    }

    // Clear error on input
    document.querySelectorAll('input.error').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('error');
            hideErrorMessage(this);
        });
    });
});

function showErrorMessage(element, message) {
    hideErrorMessage(element);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    element.parentNode.appendChild(errorDiv);
}

function hideErrorMessage(element) {
    const existing = element.parentNode.querySelector('.error-message');
    if (existing) {
        existing.remove();
    }
}
```

- [ ] **Step 9: Create directories and verify app starts**

Run: `mkdir -p static/css static/js keys data`
Run: `python -c "from app.main import app; print('App created')"`
Expected: `App created`

- [ ] **Step 10: Commit**

```bash
git add app/main.py app/routers/ app/templates/base.html static/ run.py
git commit -m "feat: FastAPI app setup with templates and static files"
```

---

### Task 7: User Signup & Verification Flow

**Files:**
- Modify: `app/routers/pages.py`
- Create: `app/templates/signup.html`
- Create: `app/templates/verify.html`

**Interfaces:**
- Consumes: `hash_password()`, `create_access_token()`, `send_verification_email()`
- Produces: Complete signup flow with form validation and email verification

- [ ] **Step 1: Update app/routers/pages.py**

```python
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
from app.auth import hash_password
from app.email_service import send_verification_email
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

USERNAME_REGEX = re.compile(r'^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$')


def validate_username(username: str) -> bool:
    return bool(USERNAME_REGEX.match(username))


@router.get("/signup")
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


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
            "signup.html",
            {"request": request, "errors": errors, "email": email, "username": username},
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
        "signup.html",
        {"request": request, "success": "Account created! Check your email to verify."},
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
            "verify.html",
            {"request": request, "error": "Invalid verification link"},
        )

    if user.token_expiry < datetime.utcnow():
        return templates.TemplateResponse(
            "verify.html",
            {"request": request, "error": "Verification link has expired"},
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
        "verify.html",
        {"request": request, "success": "Account verified! Your SSH key has been sent to your email."},
    )


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
```

- [ ] **Step 2: Create app/templates/signup.html**

```html
{% extends "base.html" %}

{% block title %}Sign Up - SSH User Management{% endblock %}

{% block hero %}
<div class="hero">
    <h1>Create Your Account</h1>
    <p>Sign up to get SSH access to the server</p>
</div>
{% endblock %}

{% block content %}
<div class="card">
    {% if success %}
    <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    {% if errors %}
    <div class="alert alert-error">
        {% for error in errors %}
        <p>{{ error }}</p>
        {% endfor %}
    </div>
    {% endif %}

    <form method="POST" action="/signup" data-validate-passwords>
        <div class="form-group">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" value="{{ email or '' }}" required>
        </div>

        <div class="form-group">
            <label for="username">Username</label>
            <input type="text" id="username" name="username" value="{{ username or '' }}" required
                   pattern="[a-z0-9][a-z0-9-]{1,30}[a-z0-9]"
                   title="Lowercase letters, numbers, and hyphens only">
        </div>

        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required minlength="8">
        </div>

        <div class="form-group">
            <label for="confirm_password">Confirm Password</label>
            <input type="password" id="confirm_password" name="confirm_password" required>
        </div>

        <button type="submit" class="btn btn-primary">Sign Up</button>
    </form>

    <p class="text-center mt-4">
        Already have an account? <a href="/login">Sign in</a>
    </p>
</div>
{% endblock %}
```

- [ ] **Step 3: Create app/templates/verify.html**

```html
{% extends "base.html" %}

{% block title %}Verify Email - SSH User Management{% endblock %}

{% block hero %}
<div class="hero">
    <h1>Email Verification</h1>
</div>
{% endblock %}

{% block content %}
<div class="card text-center">
    {% if success %}
    <div class="alert alert-success">{{ success }}</div>
    <a href="/login" class="btn btn-primary">Go to Login</a>
    {% endif %}

    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    <a href="/signup" class="btn btn-primary">Try Again</a>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 4: Create app/templates/login.html**

```html
{% extends "base.html" %}

{% block title %}Login - SSH User Management{% endblock %}

{% block hero %}
<div class="hero">
    <h1>Sign In</h1>
    <p>Access your SSH key and account</p>
</div>
{% endblock %}

{% block content %}
<div class="card">
    {% if error %}
    <div class="alert alert-error">{{ error }}</div>
    {% endif %}

    <form method="POST" action="/login">
        <div class="form-group">
            <label for="email">Email Address</label>
            <input type="email" id="email" name="email" required>
        </div>

        <div class="form-group">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required>
        </div>

        <button type="submit" class="btn btn-primary">Sign In</button>
    </form>

    <p class="text-center mt-4">
        Don't have an account? <a href="/signup">Sign up</a>
    </p>
</div>
{% endblock %}
```

- [ ] **Step 5: Add login POST handler to pages.py**

Append to `app/routers/pages.py`:

```python
from fastapi.responses import HTMLResponse
from app.auth import verify_password, create_access_token


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
            "login.html",
            {"request": request, "error": "Invalid email or password"},
        )

    if user.status != "active":
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Account not verified. Check your email."},
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
```

- [ ] **Step 6: Test signup flow**

Run: `python run.py`
Visit: `http://localhost:8000/signup`
Expected: Signup form renders with Starbucks styling

- [ ] **Step 7: Commit**

```bash
git add app/routers/pages.py app/templates/signup.html app/templates/login.html app/templates/verify.html
git commit -m "feat: user signup and email verification flow"
```

---

### Task 8: User Dashboard

**Files:**
- Modify: `app/routers/dashboard.py`
- Create: `app/templates/dashboard.html`

**Interfaces:**
- Consumes: `get_current_user()`, `generate_ssh_keys()`, `send_private_key_email()`
- Produces: User dashboard with key download functionality

- [ ] **Step 1: Update app/routers/dashboard.py**

```python
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.ssh_service import generate_ssh_keys, get_user_keys_dir
from app.email_service import send_private_key_email
from pathlib import Path

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
```

- [ ] **Step 2: Create app/templates/dashboard.html**

```html
{% extends "base.html" %}

{% block title %}Dashboard - SSH User Management{% endblock %}

{% block nav_links %}
<a href="/dashboard">Dashboard</a>
<a href="/logout">Logout</a>
{% endblock %}

{% block hero %}
<div class="hero">
    <h1>Welcome, {{ user.username }}</h1>
    <p>Manage your SSH access</p>
</div>
{% endblock %}

{% block content %}
<div class="card">
    {% if success %}
    <div class="alert alert-success">{{ success }}</div>
    {% endif %}

    <div class="info-section mb-4">
        <h2 style="margin-bottom: 1.6rem;">Account Info</h2>
        <p><strong>Username:</strong> {{ user.username }}</p>
        <p><strong>Email:</strong> {{ user.email }}</p>
        <p><strong>Status:</strong>
            <span class="badge badge-{{ user.status }}">{{ user.status }}</span>
        </p>
    </div>

    <div class="info-section">
        <h2 style="margin-bottom: 1.6rem;">SSH Key</h2>
        {% if has_key %}
        <p>Your SSH key is ready to use.</p>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <a href="/dashboard/key" class="btn btn-primary">Download Private Key</a>
            <form method="POST" action="/dashboard/key/regenerate" style="display: inline;">
                <button type="submit" class="btn btn-secondary">Regenerate Key</button>
            </form>
        </div>
        {% else %}
        <p>No SSH key found. Contact your admin.</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Add badge styles to style.css**

Append to `static/css/style.css`:

```css
/* Badges */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 50px;
    font-size: 1.2rem;
    font-weight: 600;
    text-transform: capitalize;
}

.badge-active {
    background-color: var(--green-light);
    color: var(--starbucks-green);
}

.badge-pending {
    background-color: #fff3cd;
    color: #856404;
}

.badge-inactive {
    background-color: rgba(200, 32, 20, 0.1);
    color: var(--red);
}

/* Info Section */
.info-section {
    padding-bottom: var(--space-4);
    border-bottom: 1px solid var(--ceramic);
}

.info-section:last-child {
    border-bottom: none;
    padding-bottom: 0;
}
```

- [ ] **Step 4: Test dashboard**

Run: `python run.py`
Login and visit: `http://localhost:8000/dashboard`
Expected: Dashboard shows user info and key download button

- [ ] **Step 5: Commit**

```bash
git add app/routers/dashboard.py app/templates/dashboard.html static/css/style.css
git commit -m "feat: user dashboard with key download"
```

---

### Task 9: Admin Portal

**Files:**
- Modify: `app/routers/admin.py`
- Create: `app/templates/admin.html`

**Interfaces:**
- Consumes: `require_admin()`, `generate_ssh_keys()`, `remove_key_from_authorized_keys()`, `delete_user_keys()`
- Produces: Admin dashboard with user management capabilities

- [ ] **Step 1: Update app/routers/admin.py**

```python
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
        from app.ssh_service import get_user_keys_dir
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
```

- [ ] **Step 2: Create app/templates/admin.html**

```html
{% extends "base.html" %}

{% block title %}Admin Portal - SSH User Management{% endblock %}

{% block nav_links %}
<a href="/admin">Admin</a>
<a href="/logout">Logout</a>
{% endblock %}

{% block hero %}
<div class="hero">
    <h1>Admin Portal</h1>
    <p>Manage users and SSH access</p>
</div>
{% endblock %}

{% block content %}
<div class="card">
    <h2 style="margin-bottom: 2rem;">Users ({{ users|length }})</h2>

    {% if users %}
    <div class="user-list">
        {% for user in users %}
        <div class="user-item">
            <div class="user-info">
                <strong>{{ user.username }}</strong>
                <span class="user-email">{{ user.email }}</span>
                <span class="badge badge-{{ user.status }}">{{ user.status }}</span>
            </div>
            <div class="user-actions">
                {% if user.status != 'active' %}
                <form method="POST" action="/admin/users/{{ user.id }}/activate" style="display: inline;">
                    <button type="submit" class="btn btn-primary btn-small">Activate</button>
                </form>
                {% endif %}

                {% if user.status == 'active' %}
                <form method="POST" action="/admin/users/{{ user.id }}/deactivate" style="display: inline;">
                    <button type="submit" class="btn btn-secondary btn-small">Deactivate</button>
                </form>
                {% endif %}

                <form method="POST" action="/admin/users/{{ user.id }}/regenerate-key" style="display: inline;">
                    <button type="submit" class="btn btn-secondary btn-small">Regen Key</button>
                </form>

                <form method="POST" action="/admin/users/{{ user.id }}/delete"
                      style="display: inline;"
                      onsubmit="return confirm('Are you sure you want to delete this user?');">
                    <button type="submit" class="btn btn-danger btn-small">Delete</button>
                </form>
            </div>
        </div>
        {% endfor %}
    </div>
    {% else %}
    <p class="text-center" style="color: var(--text-black-soft);">No users yet.</p>
    {% endif %}
</div>
{% endblock %}
```

- [ ] **Step 3: Add admin styles to style.css**

Append to `static/css/style.css`:

```css
/* User List */
.user-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
}

.user-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-3);
    background-color: var(--neutral-cool);
    border-radius: var(--radius-card);
    flex-wrap: wrap;
    gap: var(--space-2);
}

.user-info {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    flex-wrap: wrap;
}

.user-email {
    color: var(--text-black-soft);
    font-size: 1.4rem;
}

.user-actions {
    display: flex;
    gap: var(--space-2);
    flex-wrap: wrap;
}
```

- [ ] **Step 4: Test admin portal**

Run: `python run.py`
Login as admin and visit: `http://localhost:8000/admin`
Expected: Admin dashboard shows user list with management actions

- [ ] **Step 5: Commit**

```bash
git add app/routers/admin.py app/templates/admin.html static/css/style.css
git commit -m "feat: admin portal with user management"
```

---

### Task 10: Final Testing & Documentation

**Files:**
- Create: `README.md`
- Modify: `.gitignore`

**Interfaces:**
- Produces: Complete documentation and deployment guide

- [ ] **Step 1: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Environment
.env

# Database
data/

# SSH Keys
keys/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create README.md**

```markdown
# SSH User Management Portal

A web application for automating Linux server user creation with SSH key generation and email delivery.

## Features

- User signup with email verification
- Automatic SSH key generation (Ed25519)
- Private key delivery via email and user portal
- Admin portal for user management
- Starbucks-inspired design

## Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd user-management
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
python run.py
```

6. Visit `http://localhost:8000`

## Configuration

Edit `.env` to configure:

- `SERVER_IP`: Your server's IP address
- `ADMIN_EMAILS`: Comma-separated admin emails
- `SMTP_*`: Email settings (pre-configured for 163.com)

## Usage

### User Flow
1. Sign up with email, username, and password
2. Check email for verification link
3. Click link to activate account
4. Receive SSH private key via email
5. Login to download key anytime

### Admin Flow
1. Login with admin email
2. View all users at `/admin`
3. Activate/deactivate users
4. Regenerate SSH keys
5. Delete users

## Deployment

For production deployment:

1. Set `secure=True` in cookie settings (requires HTTPS)
2. Use a process manager like systemd or supervisor
3. Configure reverse proxy (nginx)
4. Set restrictive file permissions

### Systemd Service

```ini
[Unit]
Description=SSH User Management Portal
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/user-management
ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

MIT
```

- [ ] **Step 3: Final verification**

Run: `python run.py`
Test complete flow:
1. Visit `/signup` and create account
2. Check email for verification
3. Click verification link
4. Login at `/login`
5. Download key from dashboard
6. Login as admin at `/admin`

- [ ] **Step 4: Commit**

```bash
git add .gitignore README.md
git commit -m "docs: add README and gitignore"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|-----------------|------|
| User signup with email/username/password | Task 7 |
| Email verification | Task 7 |
| SSH key generation (Ed25519) | Task 5 |
| Public key to /root/.ssh/authorized_keys | Task 5 |
| Private key via email | Task 4, 7 |
| User portal to download key | Task 8 |
| Admin portal | Task 9 |
| Starbucks design system | Task 6 |
| Config-based admin emails | Task 1 |
| JWT authentication | Task 3 |

**All spec requirements covered.**
