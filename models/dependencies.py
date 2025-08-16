

# --- BEGIN: ensure Base is exported for tests ---
try:
    from sqlalchemy.orm import declarative_base
except Exception:
    # Fallback for older SQLAlchemy
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
# --- END: ensure Base is exported for tests ---


def utcnow():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)
