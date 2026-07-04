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
