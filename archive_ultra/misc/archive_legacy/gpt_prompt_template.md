# GPT Refactoring Prompt Template

## Standard Format for AI-Assisted Code Fixes

Use this exact format for each isolated issue:

```
You are assisting with a FastAPI legal document automation project using Python 3.11, Pydantic v2, and modern type annotations.

**ISSUE DETAILS:**
- File: `[exact file path]`
- Line: [line number or range]
- Problem: "[exact error message or description]"
- Category: [Type Safety/Migration/Import Issues/Code Cleanup]
- Suggested fix: "[specific action to take]"

**REQUIREMENTS:**
1. Maintain original logic and functionality
2. Use modern Python 3.11+ patterns
3. Follow Pydantic v2 syntax
4. Preserve all existing imports unless removing unused ones
5. Return only the corrected code block with minimal context

**EXPECTED RESPONSE:**
1. Corrected code block with changes highlighted
2. Commit message (format: "Fix: [brief description]")
3. Brief explanation of logic (2-3 sentences max)
4. Error reduction estimate

**CONTEXT:**
This is part of a systematic refactoring to reduce 6,778 Pyright errors. Each fix must be isolated, verifiable, and atomic.
```

## Example Usage:

```
You are assisting with a FastAPI legal document automation project using Python 3.11, Pydantic v2, and modern type annotations.

**ISSUE DETAILS:**
- File: `api/v1/users.py`
- Line: 14
- Problem: "Import 'NotFoundError' is not accessed (reportUnusedImport)"
- Category: Code Cleanup
- Suggested fix: "Remove unused import statement"

**REQUIREMENTS:**
1. Maintain original logic and functionality
2. Use modern Python 3.11+ patterns
3. Follow Pydantic v2 syntax
4. Preserve all existing imports unless removing unused ones
5. Return only the corrected code block with minimal context

**EXPECTED RESPONSE:**
1. Corrected code block with changes highlighted
2. Commit message (format: "Fix: [brief description]")
3. Brief explanation of logic (2-3 sentences max)
4. Error reduction estimate
```
