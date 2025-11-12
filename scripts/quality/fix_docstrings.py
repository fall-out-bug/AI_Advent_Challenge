#!/usr/bin/env python3
"""Script to automatically fix missing docstrings and type hints.

Usage: python scripts/quality/fix_docstrings.py [--dry-run]
"""

import ast
import argparse
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DocstringFixer:
    """Automatically adds missing docstrings and type hints to Python functions."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.fixed_files = 0
        self.fixed_functions = 0

    def analyze_function(self, func_node: ast.FunctionDef) -> Dict:
        """Analyze function for missing elements."""
        issues = {
            'missing_docstring': ast.get_docstring(func_node) is None,
            'missing_return_hint': func_node.returns is None,
            'missing_arg_hints': any(
                arg.annotation is None
                for arg in func_node.args.args
                if arg.arg != 'self'
            ),
        }
        return issues

    def generate_type_hint(self, arg_name: str, func_name: str) -> str:
        """Generate appropriate type hint based on naming convention."""
        if 'id' in arg_name.lower() or 'count' in arg_name.lower():
            return 'int'
        elif 'name' in arg_name.lower() or 'text' in arg_name.lower() or 'content' in arg_name.lower():
            return 'str'
        elif 'flag' in arg_name.lower() or 'enabled' in arg_name.lower():
            return 'bool'
        elif 'data' in arg_name.lower() or 'config' in arg_name.lower():
            return 'Dict[str, Any]'
        elif 'items' in arg_name.lower() or 'list' in arg_name.lower():
            return 'List[Any]'
        elif 'path' in arg_name.lower():
            return 'Path'
        else:
            # Default to str for unknown types
            return 'str'

    def generate_return_hint(self, func_name: str) -> str:
        """Generate appropriate return type hint."""
        if func_name.startswith('is_') or func_name.startswith('has_') or func_name.startswith('can_'):
            return 'bool'
        elif func_name.startswith('get_') or func_name.startswith('find_'):
            return 'Optional[Any]'
        elif func_name.startswith('list_') or func_name.startswith('find_all'):
            return 'List[Any]'
        elif func_name.startswith('create_') or func_name.startswith('build_'):
            return 'Any'
        else:
            return 'None'

    def generate_docstring(self, func_node: ast.FunctionDef) -> str:
        """Generate a basic docstring for the function."""
        func_name = func_node.name

        # Generate purpose
        purpose = f"{func_name.replace('_', ' ').capitalize()}."

        # Generate Args section
        args = []
        for arg in func_node.args.args:
            if arg.arg == 'self':
                continue
            arg_type = self.generate_type_hint(arg.arg, func_name)
            args.append(f"        {arg.arg}: {arg_type.replace('Any', 'described parameter')}")

        # Generate Returns section
        return_hint = self.generate_return_hint(func_name)
        if return_hint == 'None':
            returns = "        None"
        else:
            returns = f"        {return_hint.replace('Any', 'described result')}"

        # Build docstring
        docstring_lines = [
            '    """' + purpose,
            '    ',
            '    Purpose:',
            f'        {purpose}',
        ]

        if args:
            docstring_lines.extend([
                '    ',
                '    Args:',
            ] + args)

        docstring_lines.extend([
            '    ',
            '    Returns:',
            f'        {returns}',
            '    """'
        ])

        return '\n'.join(docstring_lines)

    def add_type_hints(self, source_lines: List[str], func_node: ast.FunctionDef) -> List[str]:
        """Add type hints to function signature."""
        # Find the function definition line
        line_idx = func_node.lineno - 1
        line = source_lines[line_idx]

        # Parse function signature
        if '(' not in line or ')' not in line:
            return source_lines

        # Extract arguments
        args_start = line.find('(') + 1
        args_end = line.rfind(')')
        args_str = line[args_start:args_end]

        # Skip if already has type hints
        if ':' in args_str and not args_str.strip().startswith('self'):
            return source_lines

        # Build new signature with type hints
        new_args = []
        for arg in func_node.args.args:
            if arg.arg == 'self':
                new_args.append('self')
            else:
                hint = self.generate_type_hint(arg.arg, func_node.name)
                new_args.append(f'{arg.arg}: {hint}')

        # Add varargs/*args if present
        if func_node.args.vararg:
            new_args.append(f'*{func_node.args.vararg.arg}')

        # Add kwargs/**kwargs if present
        if func_node.args.kwarg:
            new_args.append(f'**{func_node.args.kwarg.arg}')

        new_args_str = ', '.join(new_args)
        new_signature = f"{line[:args_start]}{new_args_str}{line[args_end:]}"

        # Add return type hint if missing
        if '->' not in new_signature and func_node.returns is None:
            return_hint = self.generate_return_hint(func_node.name)
            # Insert before closing paren and colon
            colon_pos = new_signature.rfind(':')
            if colon_pos > 0:
                new_signature = f"{new_signature[:colon_pos]} -> {return_hint}{new_signature[colon_pos:]}"

        source_lines[line_idx] = new_signature
        return source_lines

    def add_docstring(self, source_lines: List[str], func_node: ast.FunctionDef) -> List[str]:
        """Add docstring after function signature."""
        if ast.get_docstring(func_node):
            return source_lines

        # Find the function definition line
        line_idx = func_node.lineno - 1

        # Generate docstring
        docstring = self.generate_docstring(func_node)

        # Insert docstring after function signature
        source_lines.insert(line_idx + 1, '')
        source_lines.insert(line_idx + 1, docstring)
        source_lines.insert(line_idx + 1, '')

        return source_lines

    def process_file(self, file_path: Path) -> bool:
        """Process a single file to fix docstrings and type hints."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(file_path))
            source_lines = content.splitlines()

            modified = False

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    issues = self.analyze_function(node)

                    if issues['missing_docstring']:
                        source_lines = self.add_docstring(source_lines, node)
                        modified = True
                        self.fixed_functions += 1

                    if issues['missing_return_hint'] or issues['missing_arg_hints']:
                        source_lines = self.add_type_hints(source_lines, node)
                        modified = True

            if modified and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(source_lines))
                self.fixed_files += 1

            return modified

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def process_directory(self, directory: Path) -> Tuple[int, int]:
        """Process all Python files in directory."""
        python_files = list(directory.rglob('*.py'))

        # Skip test files and __init__.py files for now
        python_files = [
            f for f in python_files
            if not str(f).startswith('tests/') and f.name != '__init__.py'
        ]

        print(f"Processing {len(python_files)} Python files...")

        processed = 0
        modified = 0

        for file_path in python_files:
            if self.process_file(file_path):
                modified += 1
                print(f"Modified: {file_path}")
            processed += 1

        return processed, modified


def main():
    parser = argparse.ArgumentParser(description='Fix missing docstrings and type hints')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--directory', default='src', help='Directory to process')

    args = parser.parse_args()

    fixer = DocstringFixer(dry_run=args.dry_run)

    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Directory {directory} does not exist")
        return

    processed, modified = fixer.process_directory(directory)

    print("\nResults:")
    print(f"Files processed: {processed}")
    print(f"Files modified: {modified}")
    print(f"Functions fixed: {fixer.fixed_functions}")

    if args.dry_run:
        print("\nUse without --dry-run to apply changes")


if __name__ == '__main__':
    main()
