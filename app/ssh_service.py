import os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
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

    # Generate Ed25519 key pair using cryptography library
    private_key = Ed25519PrivateKey.generate()
    private_key_path = user_dir / "id_ed25519"
    public_key_path = user_dir / "id_ed25519.pub"

    # Write private key in OpenSSH format
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(private_key_path, "wb") as f:
        f.write(private_bytes)
    os.chmod(str(private_key_path), 0o600)

    # Write public key
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH
    )
    pub_key = f"{public_bytes.decode()} {username}@ssh-management"
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
