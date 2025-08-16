Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty

pending_total = len(remaining_files) + len(remaining_dirs)
if args.list_pending and pending_total:
    print("\nPending after execution:")
    for p in remaining_dirs:
        print(f"  [DIR]  {p.relative_to(root).as_posix()}")
    for p in remaining_files:
        print(f"  [FILE] {p.relative_to(root).as_posix()}")

print(f"Post-execution pending actions: {pending_total}")
```

Optional: after file ops, keep a **final** prune (idempotent) so any stray empties disappear before recompute:

```python
if args.prune_empty_dirs:
    prune_empty_dirs(root)  # second pass; harmless and fast
```

# Run to validate

```powershell
python scripts/cleanup_repo.py --execute --quarantine --pack --report-dir artifacts --verbose --list-pending
```

Expected: `.pytest_cache` no longer appears in pending; **Post-execution pending actions: 0**.

# Commit recommendation

I’d ship this as a discrete commit:

```powershell
git checkout -b chore/repo-hygiene
git add scripts/cleanup_repo.py artifacts/*
git commit -m "chore(cleanup): truthful pending count; ignore empty dirs; exclusions hardened"
```

If you want, I can also add a tiny CI job that runs the **dry-run** on PRs and posts the planned action summary as a comment—cheap insurance against accidental deletions.
Strong work. You’ve got one cosmetic loose end: an **empty** `.pytest_cache` still shows as pending because the planner doesn’t filter empty dirs post-op.

Here’s the surgical patch I recommend—keeps behavior identical, just makes “pending” truthful.

# Minimal patch (planner + final recompute)

Apply these edits to `scripts/cleanup_repo.py`:

```python
# add near other helpers
def is_empty_dir(d: Path) -> bool:
    try:
        next(d.iterdir())
        return False
    except StopIteration:
        return True
    except Exception:
        return False

def plan_dir_actions(root: Path):
    dirs = [d for d in root.rglob("*") if d.is_dir() and not is_excluded(d, root)]
    # only include dirs that match allowlist AND are non-empty
    return [
        d for d in dirs
        if any(r.search(d.as_posix()) for r in ALLOW_DIR) and not is_empty_dir(d)
    ]
```

And in the **final recompute** block (end of script), ensure you ignore empty dirs when reporting:

```python
remaining_files = plan_file_actions(root)
remaining_dirs  = plan_dir_actions(root)  # already filters empty
