#!/usr/bin/env python3
"""
Fix common typing issues in the Goldleaves codebase.
This script addresses the 774 problems by fixing type annotations.
"""

import os
import re
from pathlib import Path

def fix_file_typing(file_path):
    """Fix typing issues in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix 1: Add future annotations if using modern syntax
        if ('List[' in content or 'Dict[' in content) and 'from __future__ import annotations' not in content:
            # Find the first import line
            lines = content.split('\n')
            first_import_idx = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    first_import_idx = i
                    break

            if first_import_idx >= 0:
                lines.insert(first_import_idx, 'from __future__ import annotations')
                content = '\n'.join(lines)

        # Fix 2: Add typing imports if needed
        needs_typing = False
        typing_imports = set()

        if 'Dict[' in content and 'from typing import' not in content:
            typing_imports.add('Dict')
            needs_typing = True
        if 'List[' in content and 'from typing import' not in content:
            typing_imports.add('List')
            needs_typing = True
        if 'Any' in content and 'from typing import' not in content:
            typing_imports.add('Any')
            needs_typing = True
        if 'Optional[' in content and 'from typing import' not in content:
            typing_imports.add('Optional')
            needs_typing = True

        if needs_typing:
            typing_import = f"from typing import {', '.join(sorted(typing_imports))}"
            lines = content.split('\n')
            # Insert after future imports but before other imports
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('from __future__'):
                    insert_idx = i + 1
                elif line.strip().startswith('import ') or line.strip().startswith('from '):
                    if insert_idx == 0:
                        insert_idx = i
                    break

            lines.insert(insert_idx, typing_import)
            content = '\n'.join(lines)

        # Fix 3: Replace modern type annotations with compatible ones
        replacements = [
            (r'\blist\[([^\]]+)\]', r'List[\1]'),
            (r'\bdict\[([^\]]+)\]', r'Dict[\1]'),
            (r'\btuple\[([^\]]+)\]', r'Tuple[\1]'),
            (r'\bset\[([^\]]+)\]', r'Set[\1]'),
        ]

        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)

        # Fix 4: Fix lowercase built-in type annotations in function signatures
        content = re.sub(r':\s*dict\b', ': Dict[str, Any]', content)
        content = re.sub(r':\s*list\b', ': List[Any]', content)
        content = re.sub(r'response_model=Dict[str, Any]\b', 'response_model=Dict[str, Any]', content)
        content = re.sub(r'response_model=List[Any]\b', 'response_model=List[Any]', content)

        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"📝 No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Main function to fix typing issues."""
    project_root = Path(__file__).parent

    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.venv', 'venv', 'node_modules', '.pytest_cache'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)

    print(f"🔍 Found {len(python_files)} Python files to check")

    fixed_count = 0
    for file_path in python_files:
        if fix_file_typing(file_path):
            fixed_count += 1

    print(f"\n🎯 Summary:")
    print(f"   📁 Total files checked: {len(python_files)}")
    print(f"   ✅ Files fixed: {fixed_count}")
    print(f"   📝 Files unchanged: {len(python_files) - fixed_count}")

    if fixed_count > 0:
        print(f"\n🔄 Restart your Python language server to see the changes!")

if __name__ == "__main__":
    main()
