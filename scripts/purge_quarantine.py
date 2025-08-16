from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import shutil


def purge_quarantine(root: Path, days: int = 7) -> int:
    q = root / ".quarantine"
    if not q.exists():
        return 0
    cutoff = datetime.utcnow() - timedelta(days=days)
    removed = 0
    for d in q.iterdir():
        if not d.is_dir():
            continue
        try:
            ts = datetime.strptime(d.name, "%Y%m%dT%H%M%SZ")
        except Exception:
            continue
        if ts < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            removed += 1
    return removed


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    count = purge_quarantine(root, days=7)
    print(f"Purged {count} quarantine buckets older than 7 days.")
