"""Keep configured credentials out of application logs and persisted error messages."""
from app.config import settings
from app.credentials import openai_api_key


def redact_credentials(message: object) -> str:
    value = str(message)
    cfg = settings()
    credentials = [openai_api_key(), cfg.minio_access_key, cfg.minio_secret_key]
    for credential in credentials:
        if credential:
            value = value.replace(credential, "[REDACTED]")
    return value
