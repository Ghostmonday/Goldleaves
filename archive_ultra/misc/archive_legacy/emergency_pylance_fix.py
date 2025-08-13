#!/usr/bin/env python3
"""
Comprehensive Pylance Error Fix - Emergency Batch Fix
Addresses the 1000+ Pylance errors systematically
"""

from builtins import len, enumerate, any
import os
import re
import pathlib
from typing import List, Dict, Set


class EmergencyPylanceFix:
    """Emergency fixer for critical Pylance errors."""

    def __init__(self, project_root: str = "."):
        self.project_root = pathlib.Path(project_root)
        self.fixed_files = []
        self.error_count = 0

    def run_emergency_fixes(self):
        """Run all emergency fixes to reduce error count quickly."""
        print("🚨 EMERGENCY PYLANCE ERROR FIX")
        print("=" * 50)

        # Fix 1: Add __future__ imports to all Python files
        self.add_future_imports()

        # Fix 2: Replace problematic type annotations
        self.fix_type_annotations()

        # Fix 3: Add TYPE_CHECKING imports where needed
        self.add_type_checking_imports()

        # Fix 4: Fix common built-in function issues
        self.fix_builtin_functions()

        print(f"\\n✅ Emergency fixes complete!")
        print(f"Fixed {len(self.fixed_files)} files")
        print("\\nRecommendation: Restart VS Code to see improvements")

    def add_future_imports(self):
        """Add __future__ annotations import to all Python files."""
        print("\\n📦 Adding __future__ imports...")

        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Skip if already has future import
                if 'from __future__ import annotations' in content:
                    continue

                # Add future import at the top
                lines = content.split('\\n')

                # Find the right place to insert (after shebang/encoding but before other imports)
                insert_index = 0
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if (stripped.startswith('#') and
                        ('coding:' in stripped or 'encoding:' in stripped or stripped.startswith('#!'))):
                        insert_index = i + 1
                    elif stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                        break

                lines.insert(insert_index, 'from __future__ import annotations')

                # Write back
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write('\\n'.join(lines))

                self.fixed_files.append(str(py_file))
                print(f"  ✓ {py_file.relative_to(self.project_root)}")

            except Exception as e:
                print(f"  ✗ Error fixing {py_file}: {e}")

    def fix_type_annotations(self):
        """Fix problematic type annotations."""
        print("\\n🔧 Fixing type annotations...")

        # Common type fixes
        type_fixes = [
            (r'-> Optional\\[dict\\]', '-> Optional[Dict[str, Any]]'),
            (r'-> dict', '-> Dict[str, Any]'),
            (r'-> list', '-> List[Any]'),
            (r': dict', ': Dict[str, Any]'),
            (r': list', ': List[Any]'),
        ]

        for py_file in self.project_root.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Apply type fixes
                for pattern, replacement in type_fixes:
                    content = re.sub(pattern, replacement, content)

                # Add typing imports if types are used but not imported
                if ('Dict[' in content or 'List[' in content or 'Optional[' in content):
                    if 'from typing import' not in content and 'import typing' not in content:
                        # Find where to insert typing import
                        lines = content.split('\\n')
                        insert_index = 0

                        for i, line in enumerate(lines):
                            if line.strip().startswith('from __future__'):
                                insert_index = i + 1
                            elif line.strip().startswith('from ') or line.strip().startswith('import '):
                                insert_index = i
                                break

                        lines.insert(insert_index, 'from typing import Dict, List, Optional, Any, Union')
                        content = '\\n'.join(lines)

                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ {py_file.relative_to(self.project_root)}")

            except Exception as e:
                print(f"  ✗ Error fixing types in {py_file}: {e}")

    def add_type_checking_imports(self):
        """(Restored) No-op: previous autogenerated block was corrupted; skipping.
        This script is a developer tool and not required for runtime.
        """
        print("\n🔄 Skipping TYPE_CHECKING import pass (restored stub).")
        return
