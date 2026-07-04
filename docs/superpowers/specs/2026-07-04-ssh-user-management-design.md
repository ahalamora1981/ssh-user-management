# SSH User Management Portal — Design Spec

## Overview

A self-hosted web application for managing Linux server user accounts with SSH key-based authentication. The system automates user signup, email verification, SSH key generation, and key delivery.

**Stack**: Python + FastAPI + Jinja2 + SQLite + paramiko/cryptography
**Design Theme**: Starbucks-inspired (warm cream/green palette, pill buttons, layered shadows)

---

## Core Features

### 1. User Signup

- Fields: Email, Username, Password (input twice with mask)
- Password validation: min 8 chars, must include letters and numbers
- Username validation: lowercase alphanumeric + hyphens, 3-32 chars
- On submit: create user record with `status=pending`, generate verification token, send verification email

### 2. Email Verification

- Verification link format: `/verify/{token}`
- Token expires after 24 hours
- On click: set `status=active`, generate SSH key pair, copy public key to `/root/.ssh/authorized_keys`, send private key email
- Show success/error message on verification page

### 3. SSH Key Generation & Delivery

- Algorithm: Ed25519 (modern, secure, compact)
- Key storage: `/var/lib/user-management/keys/{username}/`
  - `id_ed25519` (private key, chmod 600)
  - `id_ed25519.pub` (public key)
- Public key appended to `/root/.ssh/authorized_keys` with comment `# {username}`
- Private key sent via email as `.pem` attachment
- Private key also downloadable from user portal

### 4. User Portal

- Login with email + password
- Dashboard shows:
  - Username, email, account status
  - "Download Private Key" button
  - "Regenerate Key" option (requires re-verification)
- JWT-based session (httpOnly cookie)

### 5. Admin Portal

- Accessible only to configured admin email(s)
- Features:
  - List all users (search, filter by status)
  - View user details
  - Manually activate/deactivate users
  - Regenerate SSH keys for a user
  - Delete user (removes keys from server + database)
- Admin credentials loaded from `.env` file

---

## Data Model

### users table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| email | TEXT UNIQUE | User email address |
| username | TEXT UNIQUE | SSH username |
| password_hash | TEXT | bcrypt hashed password |
| status | TEXT | pending / active / inactive |
| verification_token | TEXT | Email verification token |
| token_expiry | DATETIME | Token expiration time |
| created_at | DATETIME | Account creation time |
| updated_at | DATETIME | Last update time |

### admin_users table

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| email | TEXT UNIQUE | Admin email from config |

---

## API Routes

### Public Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Redirect to signup or dashboard |
| GET | `/signup` | Signup form |
| POST | `/signup` | Process signup |
| GET | `/verify/{token}` | Email verification |
| GET | `/login` | Login form |
| POST | `/login` | Process login |
| GET | `/logout` | Clear session |

### User Routes (authenticated)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard` | User dashboard |
| GET | `/dashboard/key` | Download private key |
| POST | `/dashboard/key/regenerate` | Regenerate SSH keys |

### Admin Routes (admin only)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin` | Admin dashboard |
| GET | `/admin/users` | List all users |
| GET | `/admin/users/{id}` | User details |
| POST | `/admin/users/{id}/activate` | Activate user |
| POST | `/admin/users/{id}/deactivate` | Deactivate user |
| POST | `/admin/users/{id}/regenerate-key` | Regenerate keys |
| POST | `/admin/users/{id}/delete` | Delete user |

---

## Design System (Starbucks-Inspired)

### Color Tokens

| Token | Hex | Usage |
|-------|-----|-------|
| Starbucks Green | `#006241` | Headings, brand |
| Green Accent | `#00754A` | Primary CTAs, links |
| House Green | `#1E3932` | Footer, feature bands |
| Neutral Warm | `#f2f0eb` | Page canvas |
| Ceramic | `#edebe9` | Section separators |
| White | `#ffffff` | Cards, modals |
| Text Black | `rgba(0,0,0,0.87)` | Primary text |
| Text Black Soft | `rgba(0,0,0,0.58)` | Secondary text |
| Text White Soft | `rgba(255,255,255,0.70)` | Text on dark bg |
| Gold | `#cba258` | Admin badge only |
| Red | `#c82014` | Errors, destructive |

### Typography

- **Primary Font**: Inter (Google Fonts) — substitute for SoDoSans
- **Letter Spacing**: `-0.01em` globally
- **Weights**: 400 (body), 600 (headings, buttons)

### Components

- **Buttons**: Full-pill `50px` radius, `scale(0.95)` active
- **Cards**: White bg, `12px` radius, layered shadow
- **Inputs**: Floating label, green accent on focus
- **Nav**: House Green bg, white text

### Page Layout

```
┌──────────────────────────────────────┐
│  Nav (House Green)                   │
├──────────────────────────────────────┤
│  Hero Band (Starbucks Green)         │
│  Title + Description                 │
├──────────────────────────────────────┤
│  Content Section (Neutral Warm)      │
│  ┌──────────────────────────────┐    │
│  │  Card (White)                │    │
│  │  Form / Dashboard            │    │
│  └──────────────────────────────┘    │
├──────────────────────────────────────┤
│  Footer (House Green)                │
└──────────────────────────────────────┘
```

---

## Email Templates

### Verification Email

```
Subject: Verify your SSH account

Hi {username},

Welcome to SSH User Management! Please verify your email to activate your account.

[Verify Email] button → /verify/{token}

This link expires in 24 hours.

If you didn't create this account, ignore this email.
```

### Private Key Email

```
Subject: Your SSH Private Key

Hi {username},

Your SSH account is now active. Your private key is attached to this email.

⚠️ Keep this key safe and never share it. If compromised, contact your admin immediately.

Connection: ssh -i {filename} root@{server_ip}
```

---

## File Structure

```
user-management/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, startup
│   ├── config.py            # Settings, .env loading
│   ├── database.py          # SQLite connection
│   ├── models.py            # SQLAlchemy models
│   ├── auth.py              # JWT, password hashing
│   ├── email_service.py     # SMTP email sending
│   ├── ssh_service.py       # Key generation, server setup
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # Signup, login, verify
│   │   ├── dashboard.py     # User portal
│   │   └── admin.py         # Admin portal
│   └── templates/
│       ├── base.html        # Layout template
│       ├── signup.html
│       ├── login.html
│       ├── verify.html
│       ├── dashboard.html
│       ├── admin/
│       │   ├── index.html
│       │   └── users.html
│       └── emails/
│           ├── verification.html
│           └── private_key.html
├── static/
│   ├── css/
│   │   └── style.css        # Starbucks-inspired styles
│   └── js/
│       └── main.js          # Form validation, interactions
├── keys/                    # SSH key storage (gitignored)
├── .env.example             # Environment variables template
├── requirements.txt
├── run.py                   # Entry point
└── README.md
```

---

## Environment Variables (.env)

```
# Database
DATABASE_URL=sqlite:///./data/users.db

# JWT
SECRET_KEY=<random-64-char-string>
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Email (SMTP)
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=taojundev@163.com
SMTP_PASSWORD=LAvnA37TqKyc5Ktm
SENDER_EMAIL=taojundev@163.com
SENDER_NAME=SSH User Management

# Server
SERVER_IP=your-server-ip
KEYS_DIR=./keys

# Admin (comma-separated emails)
ADMIN_EMAILS=admin@example.com
```

---

## Security Considerations

1. Passwords hashed with bcrypt (12 rounds)
2. JWT tokens in httpOnly, secure cookies
3. SSH private keys stored with chmod 600
4. Verification tokens are single-use, time-limited
5. CSRF protection on all forms
6. Rate limiting on login/signup endpoints
7. Admin routes check against configured email list

---

## Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
jinja2==3.1.2
python-multipart==0.0.6
sqlalchemy==2.0.23
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
paramiko==3.4.0
aiosmtplib==3.0.1
python-dotenv==1.0.0
```

---

## Future Enhancements (Out of Scope)

- Multi-server SSH key deployment
- Key expiration/rotation
- User self-service key regeneration without admin
- LDAP/SSO integration
- Audit logging dashboard
