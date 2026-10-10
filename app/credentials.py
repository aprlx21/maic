"""Load the provider credential only in the worker when it is about to make an API call."""
import os

from dotenv import dotenv_values

from app.config import ROOT


def openai_api_key() -> str:
    value = os.environ.get("OPENAI_API_KEY")
    if value:
        return value
    return dotenv_values(ROOT / ".env", interpolate=False).get("OPENAI_API_KEY", "") or ""
