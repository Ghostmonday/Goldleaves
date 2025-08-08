import uuid
from typing import Optional

def generate_request_id() -> str:
    return str(uuid.uuid4())

def mask_email(email: str) -> str:
    """Masks an email like john.doe@example.com -> j***@e********.com"""
    try:
        local, domain = email.split('@')
        return f"{local[0]}***@{domain[0]}{'*' * (len(domain) - 2)}{domain[-1]}"
    except Exception:
        return "***"

def safe_get(d: dict, keys: list, default: Optional[str] = None):
    """Safely get nested dictionary value"""
    for key in keys:
        try:
            d = d[key]
        except (KeyError, TypeError):
            return default
    return d
