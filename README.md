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
