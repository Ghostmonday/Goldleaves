Contributing
============

Conflict-marker guardrails
--------------------------

This repository blocks accidental commits that contain Git conflict markers.

Local pre-commit hook
---------------------

You can enable the local hook to scan only staged text files:

1. Configure Git to use the repo `hooks/` folder for hooks:

   git config core.hooksPath hooks

2. Ensure the hook is executable (on Unix-like systems):

   chmod +x hooks/pre-commit

The hook will fail the commit if any staged text file contains conflict markers (<<<<<<<, =======, >>>>>>>).

CI check
--------

On push and pull requests, GitHub Actions runs a check that scans changed text files for conflict markers and fails the build if any are found.

Advanced
--------

To prefer union merges for documentation, `.gitattributes` includes:

    docs/** merge=union

You can also add language- or path-specific rules here as needed.
