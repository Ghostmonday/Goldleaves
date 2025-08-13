"""
Goldleaves repository hygiene tool (safe, idempotent, Git-aware).

Implements the Cleanup Playbook:
- Dry-run by default; prints and writes reports without modifying the tree.
- Deletes only known generated artifacts; quarantines tracked candidates by default.
- Normalizes text files (trailing ws, blank lines, final newline, BOM removal) without changing semantics.
- Optional packaging into a cleaned zip.

Usage examples:
  python scripts/cleanup_repo.py --report-dir artifacts
  python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts

Notes:
- Operates only within git repo root.
- Excludes .git directory and never touches critical source paths beyond normalization.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import re
import shutil
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]

# Allowlist deletion patterns (dirs & files)
DELETE_DIR_PATTERNS = [
    r"/(?:__pycache__)/",
    r"/\.pytest_cache/",
    r"/\.mypy_cache/",
    r"/\.ruff_cache/",
    r"/\.ipynb_checkpoints/",
    r"/\.tox/",
    r"/\.venv/",
    r"/env/",
    r"/build/",
    r"/dist/",
    r"/\.eggs/",
    r"/\.idea/",
    r"/\.vs/",
]
DELETE_FILE_PATTERNS = [
    r"\.pyc$",
    r"\.pyo$",
    r"\.pyd$",
    r"\.log$",
    r"/\.DS_Store$",
    r"/(?:~|~[^/\\]*)$",
    r"\.swp$",
    r"\.swo$",
    r"\.orig$",
    r"\.rej$",
    r"/coverage\.xml$",
    r"/\.coverage(?:\..*)?$",
]

TEXT_EXTS = {
    ".py",
    ".pyi",
    ".txt",
    ".md",
    ".toml",
    ".ini",
    ".cfg",
    ".yml",
    ".yaml",
    ".json",
    ".env",
    ".sh",
    ".ps1",
}

# Exclude these directory names anywhere in the tree (vendored/generated)
EXCLUDE_DIRS = {
    ".git",
    ".github",
    ".quarantine",
    "artifacts",
    "node_modules",
    "vendor",
    ".venv",
    ".tox",
}


def is_excluded(path: Path, root: Path) -> bool:
    """Return True if a path is under an excluded directory name anywhere in the tree."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def norm(p: str) -> str:
    return p.replace("\\", "/")


def compile_patterns(patterns: Iterable[str]) -> List[re.Pattern]:
    return [re.compile(p) for p in patterns]


ALLOW_DIR = compile_patterns(DELETE_DIR_PATTERNS)
ALLOW_FILE = compile_patterns(DELETE_FILE_PATTERNS)


def is_dir_candidate(path: Path) -> bool:
    p = norm(str(path.as_posix()) + ("/" if not str(path).endswith("/") else ""))
    return any(r.search(p) for r in ALLOW_DIR)


def is_file_candidate(path: Path) -> bool:
    p = norm(path.as_posix())
    return any(r.search(p) for r in ALLOW_FILE)


# Helper to check if a directory is empty (best-effort, safe)
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False


def plan_dir_actions(root: Path) -> List[Path]:
    """Return candidate directories that match allowlist, are non-empty, and whose contents are safe artifacts.

    Mirrors the safety check used in plan_cleanup for delete_dir actions.
    """
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    candidates: List[Path] = []
    for d in dirs:
        if not any(r.search(d.as_posix()) for r in ALLOW_DIR):
            continue
        if is_empty_dir(d):
            continue
        unsafe = False
        for c in d.rglob("*"):
            if c.is_file() and not is_file_candidate(c):
                unsafe = True
                break
        if not unsafe:
            candidates.append(d)
    return candidates


def plan_file_actions(root: Path) -> List[Path]:
    """Return candidate files to consider (allowlisted files only)."""
    files: List[Path] = []
    for p in list_all_files(root):
        if is_excluded(p, root):
            continue
        if is_file_candidate(p):
            files.append(p)
    return files


def git_tracked_files() -> set[str]:
    try:
        import subprocess

        out = subprocess.check_output(["git", "ls-files"], cwd=str(ROOT), text=True)
        return set(line.strip() for line in out.splitlines() if line.strip())
    except Exception:
        return set()


def list_all_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded dirs by name anywhere
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for name in filenames:
            p = Path(dirpath) / name
            if is_excluded(p, root):
                continue
            yield p


def _should_skip_normalize(p: Path, data: Optional[bytes] = None) -> bool:
    # Skip excluded directories
    if is_excluded(p, ROOT):
        return True
    # Size guard: skip > 512 KiB
    try:
        if p.stat().st_size > 512 * 1024:
            return True
    except Exception:
        return True
    # Skip minified and lockfiles
    name = p.name.lower()
    if (
        name.endswith(".min.js")
        or name.endswith(".min.css")
        or name in {"package-lock.json", "yarn.lock", "poetry.lock", "pipfile.lock"}
    ):
        return True
    # If data provided, treat NUL as binary
    if data is not None and b"\x00" in data:
        return True
    return False


def detect_text_mod_needed(p: Path) -> bool:
    if p.suffix.lower() not in TEXT_EXTS:
        return False
    try:
        data = p.read_bytes()
    except Exception:
        return False
    if _should_skip_normalize(p, data):
        return False
    # Detect BOM (UTF-8)
    had_bom = data.startswith(b"\xef\xbb\xbf")
    if had_bom:
        data = data[3:]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    normalized = normalize_text_content(text)
    return normalized != text or had_bom


def normalize_text_file(p: Path) -> bool:
    try:
        data = p.read_bytes()
    except Exception:
        return False
    if _should_skip_normalize(p, data):
        return False
    had_bom = data.startswith(b"\xef\xbb\xbf")
    if had_bom:
        data = data[3:]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    normalized = normalize_text_content(text)
    if normalized != text or had_bom:
        p.write_text(normalized, encoding="utf-8", newline="\n")
        return True
    return False


def normalize_text_content(text: str) -> str:
    # Strip trailing spaces/tabs on each line
    lines = [re.sub(r"[ \t]+$", "", ln) for ln in text.splitlines()]
    # Collapse >2 consecutive blank lines to at most 2
    collapsed: List[str] = []
    blank_run = 0
    for ln in lines:
        if ln.strip() == "":
            blank_run += 1
            if blank_run <= 2:
                collapsed.append(ln)
        else:
            blank_run = 0
            collapsed.append(ln)
    normalized = "\n".join(collapsed) + "\n"  # ensure exactly one final newline
    return normalized


@dataclass
class Action:
    action: str  # delete_file | delete_dir | quarantine_file | modify_file
    path: Path
    size: int = 0
    details: str = ""


def plan_cleanup(root: Path) -> Tuple[List[Action], List[Action], List[Action]]:
    tracked = git_tracked_files()
    tracked_posix = {norm(p) for p in tracked}

    delete_or_quarantine: List[Action] = []
    modify: List[Action] = []
    delete_dirs: List[Action] = []

    # File candidates
    for p in list_all_files(root):
        if is_excluded(p, root):
            continue
        posix_rel = norm(p.relative_to(root).as_posix())
        if is_file_candidate(p):
            size = p.stat().st_size if p.exists() else 0
            if posix_rel in tracked_posix:
                delete_or_quarantine.append(Action("quarantine_file", p, size, "tracked cache/artifact file"))
            else:
                delete_or_quarantine.append(Action("delete_file", p, size, "generated cache/artifact"))
        else:
            # Consider for text normalization
            if p.suffix.lower() in TEXT_EXTS and detect_text_mod_needed(p):
                modify.append(Action("modify_file", p, 0, "text normalization"))

    # Directory candidates (delete dirs only if all contents are safe artifacts)
    for d in [p for p in root.rglob("*") if p.is_dir()]:
        if is_excluded(d, root):
            continue
        if not is_dir_candidate(d):
            continue
        # Check contents
        contents = list(d.rglob("*"))
        if not contents:
            # Skip empty directories; a prune pass handles them and they shouldn't appear as pending
            continue
        unsafe = False
        total_size = 0
        for c in contents:
            if c.is_file():
                total_size += c.stat().st_size
                if not is_file_candidate(c):
                    # If a file inside the dir is not a removable artifact, don't delete dir wholesale
                    unsafe = True
                    break
        if not unsafe:
            delete_dirs.append(Action("delete_dir", d, total_size, "generated dir"))

    return delete_or_quarantine, delete_dirs, modify


def write_reports(actions: List[Action], dir_actions: List[Action], mods: List[Action], report_dir: Path, ts: str, dry_run: bool) -> Tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    csv_path = report_dir / f"cleanup_ledger_{ts}.csv"
    md_path = report_dir / f"cleanup_report_{ts}.md"

    all_actions = actions + dir_actions + mods

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "action", "path", "bytes", "details"])
        for a in all_actions:
            details = ("planned (dry-run); " if dry_run else "") + a.details
            writer.writerow([ts, a.action, a.path.relative_to(ROOT).as_posix(), a.size, details])

    # Markdown summary
    total_bytes = sum(a.size for a in actions + dir_actions if a.action in {"delete_file", "delete_dir", "quarantine_file"})
    summary_lines = []
    summary_lines.append(f"# Repo Cleanup Report\n")
    summary_lines.append(f"- Run timestamp: {ts}")
    summary_lines.append(f"- Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}")
    summary_lines.append(f"- Total actions: {len(all_actions)}")
    summary_lines.append(f"- Files/dirs removed or quarantined (count): {len([a for a in actions+dir_actions if a.action in {'delete_file','delete_dir','quarantine_file'}])}")
    summary_lines.append(f"- Files modified (count): {len(mods)}")
    summary_lines.append(f"- Estimated bytes freed: {human_bytes(total_bytes)}\n")

    summary_lines.append("## Line-item ledger\n")
    summary_lines.append("| action | path | bytes | details |\n|---|---|---:|---|")
    for a in all_actions:
        details = ("planned (dry-run); " if dry_run else "") + a.details
        summary_lines.append(f"| {a.action} | {a.path.relative_to(ROOT).as_posix()} | {a.size} | {details} |")

    md_path.write_text("\n".join(summary_lines), encoding="utf-8")
    return csv_path, md_path


def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024
        i += 1
    return f"{f:.1f} {units[i]}"


IS_WINDOWS = os.name == "nt"


def _lp(p: Path) -> str:
    s = str(p.resolve())
    if IS_WINDOWS and not s.startswith("\\\\?\\"):
        if s.startswith("\\\\"):  # UNC
            return "\\\\?\\UNC\\" + s[2:]
        return "\\\\?\\" + s
    return s


def _clear_attrs(path: Path):
    if IS_WINDOWS and path.exists():
        try:
            import ctypes

            FILE_ATTRIBUTE_NORMAL = 0x80
            ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_NORMAL)
        except Exception:
            os.system(f'attrib -r -h -s "{path}" >NUL 2>&1')


def prune_empty_dirs(root: Path, max_passes: int = 3, verbose: bool = False) -> int:
    removed = 0
    for _ in range(max_passes):
        pass_removed = 0
    for d in sorted([p for p in root.rglob("*") if p.is_dir() and not is_excluded(p, root)], key=lambda x: len(x.parts), reverse=True):
            try:
                if not any(d.iterdir()):
                    _clear_attrs(d)
                    os.rmdir(_lp(d))
                    pass_removed += 1
                    removed += 1
                    if verbose:
                        print(f"[prune] delete_dir {d}")
            except Exception:
                pass
        if pass_removed == 0:
            break
    return removed


def force_delete_file(p: Path, retries: int = 5, delay: float = 0.2, verbose: bool = False) -> bool:
    for i in range(retries):
        try:
            _clear_attrs(p)
            os.remove(_lp(p))
            if verbose:
                print(f"[ok] delete_file {p}")
            return True
        except FileNotFoundError:
            return True
        except Exception:
            time.sleep(delay * (i + 1))
    if verbose:
        print(f"[fail] delete_file {p}")
    return False


def move_to_quarantine(src: Path, dst: Path, retries: int = 5, delay: float = 0.2, verbose: bool = False) -> bool:
    for i in range(retries):
        try:
            _clear_attrs(src)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(_lp(src), _lp(dst))
            if verbose:
                print(f"[ok] quarantine_file {src} -> {dst}")
            return True
        except Exception:
            time.sleep(delay * (i + 1))
    if verbose:
        print(f"[fail] quarantine_file {src}")
    return False


def execute_actions(actions: List[Action], dir_actions: List[Action], mods: List[Action], quarantine: bool, verbose: bool = False) -> None:
    # Delete directories first for explicit cache/build dirs
    for d in sorted(dir_actions, key=lambda x: len(x.path.as_posix().split("/")), reverse=True):
        if d.action == "delete_dir":
            try:
                if is_excluded(d.path, ROOT):
                    continue
                shutil.rmtree(_lp(d.path), ignore_errors=True)
                if verbose:
                    print(f"[ok] delete_dir {d.path}")
            except Exception:
                if verbose:
                    print(f"[fail] delete_dir {d.path}")
    # Delete/quarantine files
    for a in actions:
        if a.action == "quarantine_file" and quarantine:
            qpath = ROOT / ".quarantine" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) / a.path.relative_to(ROOT)
            move_to_quarantine(a.path, qpath, verbose=verbose)
        elif a.action == "delete_file":
            force_delete_file(a.path, verbose=verbose)
        elif a.action == "quarantine_file" and not quarantine:
            # Default safety: quarantine tracked artifacts even if quarantine flag omitted
            qpath = ROOT / ".quarantine" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) / a.path.relative_to(ROOT)
            move_to_quarantine(a.path, qpath, verbose=verbose)
    # Normalize text files
    for m in mods:
        if is_excluded(m.path, ROOT):
            continue
        if normalize_text_file(m.path) and verbose:
            print(f"[ok] modify_file {m.path}")
    # Final prune pass for empty directories
    prune_empty_dirs(ROOT, verbose=verbose)


def safe_unlink(p: Path) -> None:
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass


def safe_rmtree(p: Path) -> None:
    try:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass


def safe_rename(src: Path, dst: Path) -> None:
    try:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
    except Exception:
        pass


def create_zip(ts: str, dest_dir: Path) -> Path:
    zip_path = dest_dir / f"Goldleaves_cleaned_{ts}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in list_all_files(ROOT):
            # Skip excluded directories entirely
            if is_excluded(p, ROOT):
                continue
            rel = p.relative_to(ROOT)
            zf.write(p, rel.as_posix())
    return zip_path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Repo hygiene and normalization tool (safe by default)")
    parser.add_argument("--execute", action="store_true", help="Perform actions; otherwise dry-run only")
    parser.add_argument("--quarantine", action="store_true", help="Quarantine tracked artifact files instead of deleting (default safety)")
    parser.add_argument("--pack", action="store_true", help="Package cleaned tree into a zip (only with --execute)")
    parser.add_argument("--report-dir", default="artifacts", help="Directory to write CSV/Markdown reports")
    parser.add_argument("--verbose", action="store_true", help="Print per-item actions and outcomes")
    parser.add_argument("--dry-run", action="store_true", help="Alias for running without --execute")
    parser.add_argument("--list-pending", action="store_true", help="List unresolved paths after execution")
    args = parser.parse_args(argv)

    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    report_dir = (ROOT / args.report_dir).resolve()

    delete_or_quarantine, delete_dirs, modify = plan_cleanup(ROOT)

    # Write reports even in dry-run so maintainers can review
    dry = (not args.execute) or args.dry_run
    csv_path, md_path = write_reports(delete_or_quarantine, delete_dirs, modify, report_dir, ts, dry_run=dry)

    print(f"Report written: {md_path}")
    print(f"Ledger written: {csv_path}")
    print(f"Planned actions: {len(delete_or_quarantine) + len(delete_dirs) + len(modify)}")

    if dry:
        print("Dry-run complete. Re-run with --execute after reviewing the report.")
        return 0

    execute_actions(delete_or_quarantine, delete_dirs, modify, quarantine=True if args.quarantine else True, verbose=args.verbose)

    # Optional final prune pass (idempotent) so stray empties are removed before recompute
    prune_empty_dirs(ROOT, verbose=args.verbose)

    # Post-exec verification discovery: ignore empty dirs in pending
    remaining_files = plan_file_actions(ROOT)
    remaining_dirs = plan_dir_actions(ROOT)  # already filters empty
    pending_total = len(remaining_files) + len(remaining_dirs)
    if args.list_pending and pending_total:
        print("\nPending after execution:")
        for p in remaining_dirs:
            print(f"  [DIR]  {p.relative_to(ROOT).as_posix()}")
        for p in remaining_files:
            print(f"  [FILE] {p.relative_to(ROOT).as_posix()}")
    print(f"Post-execution pending actions: {pending_total}")

    if args.pack:
        zip_path = create_zip(ts, report_dir)
        print(f"Packaged cleaned archive: {zip_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
