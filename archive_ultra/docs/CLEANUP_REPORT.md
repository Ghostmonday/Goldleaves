# Repo Hygiene Cleanup — 2025-08-08T11:00:11.352136Z

## Policy
- Retained runtime source, configs, migrations, tests, and VS Code integration.
- Archived historical phase notes, triage/summary docs, ad-hoc scripts, and dev-only tools.
- Nothing deleted; everything pruned is in `archive/` for retrieval.

## Moves
- `current_error_report.json` → `archive/misc/current_error_report.json`
- `debug_security.py` → `archive/tools/debug_security.py`
- `docs` → `archive/docs/docs`

## Next Steps
1) Open in VS Code and run tasks as per `VS_CODE_ONBOARDING.md`.
2) If any archived file is still needed, move it back (case-by-case).
3) Optionally `pre-commit install` for guardrails.