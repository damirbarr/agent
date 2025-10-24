#!/usr/bin/env python3
"""
Script to remove whitespace-only lines from Python files.
Ensures that all blank lines have exactly 0 spaces.
"""

import os
import re
import sys

def fix_whitespace_in_file(filename):
    """Remove whitespace-only lines from a file."""
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Track if we made any changes
    changed = False

    # Fix whitespace-only lines
    for i, line in enumerate(lines):
        if re.match(r'^\s+$', line):
            lines[i] = '\n'
            changed = True

    # Only write back if we made changes
    if changed:
        print(f"Fixing whitespace in {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        return True
    return False

def find_python_files(root_dir='.'):
    """Find all Python files in the given directory tree."""
    python_files = []
    skip_dirs = ['__pycache__', '.venv', 'venv']

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip directories we don't want to process
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]

        for filename in filenames:
            if filename.endswith('.py'):
                full_path = os.path.join(dirpath, filename)
                python_files.append(full_path)

    return python_files

def main():
    """Main function to process all Python files."""
    python_files = find_python_files()
    fixed_files = 0

    for py_file in python_files:
        if fix_whitespace_in_file(py_file):
            fixed_files += 1

    print(f"\nFixed whitespace in {fixed_files} files.")

if __name__ == "__main__":
    main() 