# SSH User Management Portal

A web application for automating Linux server user creation with SSH key generation and email delivery.

## Features

- User signup with email verification
- Automatic SSH key generation (Ed25519)
- Private key delivery via email and user portal
- Admin portal for user management
- Starbucks-inspired design

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd user-management
```

2. Install dependencies with uv:
```bash
uv sync
```

Or with pip:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run the application:
```bash
uv run python run.py
```

Or with script entry point:
```bash
uv run start
```

5. Visit `http://localhost:8000`

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

## Development

### Adding Dependencies

```bash
# Add a dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name
```

### Running Tests

```bash
uv run pytest
```

### Updating Dependencies

```bash
uv lock --upgrade
uv sync
```

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
ExecStart=/path/to/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## License

MIT
