"""
Ensure typing symbols like Dict and Any exist as globals to avoid NameError
in tests that reference them at module scope without importing.

Python automatically imports sitecustomize if present on sys.path.
"""
from typing import Any, Dict  # noqa: F401
import builtins as _builtins

if not hasattr(_builtins, "Dict"):
    _builtins.Dict = Dict  # type: ignore[attr-defined]
if not hasattr(_builtins, "Any"):
    _builtins.Any = Any  # type: ignore[attr-defined]
