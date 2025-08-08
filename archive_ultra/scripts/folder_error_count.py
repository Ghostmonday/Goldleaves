import json
from collections import Counter
from pathlib import Path

with open("post_alembic_fix.json") as f:
    data = json.load(f)

folders = []
for diag in data["generalDiagnostics"]:
    file_path = diag.get("file", "")
    try:
        # Convert full path to folder name (e.g., "alembic", "services", etc.)
        folder = Path(file_path).parts[-2]
        folders.append(folder)
    except IndexError:
        continue

counts = Counter(folders)

print("📊 Error count by folder:")
for folder, count in counts.most_common():
    print(f"{folder:<20} {count}")
