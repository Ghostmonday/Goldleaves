# Contributing

## Local hooks (pre-commit)
Enable the repo’s hooks directory once per clone:
```bash
git config core.hooksPath hooks
chmod +x hooks/pre-commit
```

The pre-commit hook scans **staged text files** for Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) and blocks commits if found.

## CI guard

GitHub Actions workflow `Block merge conflict markers` scans **changed text files** on push/PR and fails if markers are present. This protects `main` even when commits are made via the GitHub UI or without local hooks.

## Docs merges

`.gitattributes` configures `docs/**` with `merge=union` to keep both sides in documentation merges, reducing manual conflict resolution.

## Repo Hygiene

We include a safe, idempotent cleanup tool to keep the tree tidy and builds reproducible.

- Script: `scripts/cleanup_repo.py`
- Exclusions: `.git/`, `.github/`, `artifacts/`, `.quarantine/`
- Deletes only known caches/artifacts; quarantines tracked candidates by default.
- Normalizes text files (trailing whitespace, blank lines <=2, final newline, BOM removal).
- Flags:
	- `--dry-run` (default if no `--execute`): plan only; write reports in `artifacts/`
	- `--execute`: perform actions
	- `--quarantine`: keep tracked artifacts under `.quarantine/<TS>/`
	- `--list-pending`: show unresolved paths after execution
	- `--pack`: zip cleaned tree to `artifacts/Goldleaves_cleaned_<TS>.zip`

CI:
- `Cleanup Dry-Run` workflow runs on PRs, uploads reports, and comments a summary.
- Quarantine retention is 7 days; a weekly purge job removes older buckets.
