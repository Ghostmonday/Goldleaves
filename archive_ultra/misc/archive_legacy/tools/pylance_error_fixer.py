#!/usr/bin/env python3
"""
Automated Pylance Error Fix Script
Systematically fixes common Pylance issues in the Goldleaves project.
"""

from __future__ import annotations
import os
import pathlib
import re
from typing import List, Set, Dict
import argparse
from builtins import set, any, enumerate  # Fix Pylance built-in recognition

class PylanceErrorFixer:
    """Automated fixer for common Pylance errors."""

    def __init__(self, project_root: str):
        self.project_root = pathlib.Path(project_root)
        self.python_dirs = set()
        self.fixed_files = []

    def add_missing_init_files(self) -> int:
        """Add __init__.py files to all Python package directories."""
        count = 0

        for root, dirs, files in os.walk(self.project_root):
            # Skip .venv, __pycache__, and other irrelevant directories
            dirs[:] = [
                d for d in dirs
                if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']
            ]

            # Check if directory contains .py files
            has_python_files = any(f.endswith('.py') for f in files)

            if has_python_files:
                init_file = pathlib.Path(root) / '__init__.py'
                if not init_file.exists():
                    init_file.touch()
                    print(f"✓ Created: {init_file.relative_to(self.project_root)}")
                    count += 1

        return count

    def fix_import_statements(self, file_path: pathlib.Path) -> bool:
        """Fix common import issues in a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Add missing typing imports if file has type hints but no typing import
            if self._needs_typing_imports(content):
                content = self._add_typing_imports(content)

            # Add missing built-in imports for commonly undefined functions
            if self._needs_builtin_imports(content):
                content = self._add_builtin_imports(content)

            # Fix __future__ imports (they should be first)
            content = self._fix_future_imports(content)

            # Save if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            print(f"✗ Error fixing {file_path}: {e}")

        return False

    def _needs_typing_imports(self, content: str) -> bool:
        """Check if file needs typing imports."""
        # Look for type hints without typing import
        has_type_hints = bool(re.search(r':\s*(List|Dict|Optional|Union|Any|Callable)', content))
        has_typing_import = 'from typing import' in content or 'import typing' in content

        return has_type_hints and not has_typing_import

    def _add_typing_imports(self, content: str) -> str:
        """Add necessary typing imports."""
        # Find what typing imports are needed
        typing_imports = set()

        type_patterns = {
            r'\bList\b': 'List',
            r'\bDict\b': 'Dict',
            r'\bOptional\b': 'Optional',
            r'\bUnion\b': 'Union',
            r'\bAny\b': 'Any',
            r'\bCallable\b': 'Callable',
            r'\bType\b': 'Type',
            r'\bGeneric\b': 'Generic',
            r'\bTypeVar\b': 'TypeVar'
        }

        for pattern, import_name in type_patterns.items():
            if re.search(pattern, content):
                typing_imports.add(import_name)

        if typing_imports:
            imports_line = f"from typing import {', '.join(sorted(typing_imports))}\n"

            # Insert after any existing imports but before the first class/function
            lines = content.split('\n')
            insert_index = self._find_import_insert_position(lines)

            lines.insert(insert_index, imports_line)
            content = '\n'.join(lines)

        return content

    def _needs_builtin_imports(self, content: str) -> bool:
        """Check if file has undefined built-in function errors."""
        # Common Pylance issues with built-ins
        builtin_functions = ['len', 'dict', 'list', 'getattr', 'property', 'type', 'str', 'int', 'bool']

        for func in builtin_functions:
            # Look for function calls that might be flagged
            if re.search(rf'\b{func}\s*\(', content):
                return True

        return False

    def _add_builtin_imports(self, content: str) -> str:
        """Add built-in imports to fix Pylance recognition issues."""
        # This is usually not needed, but can help with some Pylance issues
        builtin_imports = []

        builtin_functions = {
            r'\blen\s*\(': 'len',
            r'\bdict\s*\(': 'dict',
            r'\blist\s*\(': 'list',
            r'\bgetattr\s*\(': 'getattr',
            r'@property': 'property'
        }

        for pattern, func_name in builtin_functions.items():
            if re.search(pattern, content):
                builtin_imports.append(func_name)

        if builtin_imports:
            # Add comment explaining why this import exists
            import_line = f"# Fix Pylance built-in recognition\nfrom builtins import {', '.join(sorted(set(builtin_imports)))}\n"

            lines = content.split('\n')
            insert_index = self._find_import_insert_position(lines)

            lines.insert(insert_index, import_line)
            content = '\n'.join(lines)

        return content

    def _fix_future_imports(self, content: str) -> str:
        """Move __future__ imports to the top."""
        lines = content.split('\n')
        future_imports = []
        other_lines = []

        for line in lines:
            if line.strip().startswith('from __future__ import'):
                future_imports.append(line)
            else:
                other_lines.append(line)

        if future_imports:
            # Put future imports at the very top
            return '\n'.join(future_imports + [''] + other_lines)

        return content

    def _find_import_insert_position(self, lines: List[str]) -> int:
        """Find the best position to insert new imports."""
        # Look for the end of existing imports
        last_import_index = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or
                stripped.startswith('from ') or
                stripped.startswith('#') or
                stripped == '' or
                stripped.startswith('"""') or
                stripped.startswith("'")):
                last_import_index = i
            elif stripped and not stripped.startswith('#'):
                break

        return last_import_index + 1

    def fix_pydantic_models(self, file_path: pathlib.Path) -> bool:
        """Fix common Pydantic v2 issues."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            original_content = content

            # Replace old Config class with model_config
            content = re.sub(
                r'class Config:\s*\n\s*orm_mode\s*=\s*True',
                'model_config = ConfigDict(from_attributes=True)',
                content,
                flags=re.MULTILINE
            )

            # Add ConfigDict import if model_config is used
            if 'model_config = ConfigDict' in content and 'ConfigDict' not in content:
                if 'from pydantic import' in content:
                    content = re.sub(
                        r'from pydantic import ([^,\n]+)',
                        r'from pydantic import \1, ConfigDict',
                        content
                    )
                else:
                    # Add new import
                    lines = content.split('\n')
                    insert_index = self._find_import_insert_position(lines)
                    lines.insert(insert_index, 'from pydantic import ConfigDict')
                    content = '\n'.join(lines)

            # Save if changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True

        except Exception as e:
            print(f"✗ Error fixing Pydantic in {file_path}: {e}")

        return False

    def run_full_fix(self) -> Dict[str, int]:
        """Run all fixes across the project."""
        results = {
            'init_files_added': 0,
            'import_fixes': 0,
            'pydantic_fixes': 0,
            'total_files_processed': 0
        }

        print("🔧 Starting comprehensive Pylance error fixes...")
        print("=" * 60)

        # Phase 1: Add missing __init__.py files
        print("\n📁 Phase 1: Adding missing __init__.py files...")
        results['init_files_added'] = self.add_missing_init_files()
        print(f"✓ Added {results['init_files_added']} __init__.py files")

        # Phase 2: Fix import issues in Python files
        print("\n📦 Phase 2: Fixing import statements...")
        for py_file in self.project_root.rglob('*.py'):
            if self._should_process_file(py_file):
                results['total_files_processed'] += 1

                if self.fix_import_statements(py_file):
                    results['import_fixes'] += 1
                    print(f"✓ Fixed imports: {py_file.relative_to(self.project_root)}")

                if 'BaseModel' in py_file.read_text(encoding='utf-8'):
                    if self.fix_pydantic_models(py_file):
                        results['pydantic_fixes'] += 1
                        print(f"✓ Fixed Pydantic: {py_file.relative_to(self.project_root)}")

        print("\n" + "=" * 60)
        print("🎉 Pylance Error Fix Summary:")
        print(f"   📁 __init__.py files added: {results['init_files_added']}")
        print(f"   📦 Import fixes applied: {results['import_fixes']}")
        print(f"   🔧 Pydantic fixes applied: {results['pydantic_fixes']}")
        print(f"   📄 Total files processed: {results['total_files_processed']}")
        print("\n✅ Phase 1 fixes complete! Restart VS Code to see improvements.")

        return results

    def _should_process_file(self, file_path: pathlib.Path) -> bool:
        """Check if file should be processed."""
        # Skip virtual environment and cache directories
        path_str = str(file_path)
        skip_dirs = ['.venv', '__pycache__', '.git', 'node_modules', 'build', 'dist']

        return not any(skip_dir in path_str for skip_dir in skip_dirs)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Fix Pylance errors in Goldleaves project")
    parser.add_argument("--project-root", "-p", default=".", help="Project root directory")
    parser.add_argument("--init-only", action="store_true", help="Only add __init__.py files")

    args = parser.parse_args()

    fixer = PylanceErrorFixer(args.project_root)

    if args.init_only:
        print("📁 Adding missing __init__.py files only...")
        count = fixer.add_missing_init_files()
        print(f"✓ Added {count} __init__.py files")
    else:
        fixer.run_full_fix()


if __name__ == "__main__":
    main()
