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
