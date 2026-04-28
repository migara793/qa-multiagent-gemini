#!/usr/bin/env python3
"""
Build tree-sitter language parsers for multi-language AST support

This script downloads and compiles tree-sitter grammars for:
- Python
- JavaScript
- TypeScript

Run this once during setup or Docker build
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil


def run_command(cmd: list, cwd: str = None) -> bool:
    """Run shell command and return success status"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ {' '.join(cmd)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {' '.join(cmd)}")
        print(f"  Error: {e.stderr}")
        return False


def clone_grammar(repo_url: str, dest: Path) -> bool:
    """Clone tree-sitter grammar repository"""
    if dest.exists():
        print(f"✓ {dest.name} already exists")
        return True

    print(f"Cloning {dest.name}...")
    return run_command(['git', 'clone', '--depth=1', repo_url, str(dest)])


def build_languages():
    """Build tree-sitter language library"""
    print("\n" + "="*60)
    print("Building Tree-sitter Language Parsers")
    print("="*60 + "\n")

    # Setup directories
    script_dir = Path(__file__).parent
    vendor_dir = script_dir / 'vendor'
    build_dir = script_dir / 'build'

    vendor_dir.mkdir(exist_ok=True)
    build_dir.mkdir(exist_ok=True)

    # Grammar repositories
    grammars = {
        'tree-sitter-python': 'https://github.com/tree-sitter/tree-sitter-python.git',
        'tree-sitter-javascript': 'https://github.com/tree-sitter/tree-sitter-javascript.git',
        'tree-sitter-typescript': 'https://github.com/tree-sitter/tree-sitter-typescript.git',
    }

    # Clone grammars
    print("Step 1: Cloning grammar repositories...\n")
    grammar_paths = {}

    for name, url in grammars.items():
        dest = vendor_dir / name
        if clone_grammar(url, dest):
            grammar_paths[name] = dest
        else:
            print(f"Failed to clone {name}")
            return False

    # Build shared library
    print("\nStep 2: Building shared library...\n")

    try:
        from tree_sitter import Language

        # Language paths
        paths = [
            str(grammar_paths['tree-sitter-python']),
            str(grammar_paths['tree-sitter-javascript']),
            str(grammar_paths['tree-sitter-typescript'] / 'typescript'),
            str(grammar_paths['tree-sitter-typescript'] / 'tsx'),
        ]

        # Build library
        lib_path = build_dir / 'languages.so'
        Language.build_library(str(lib_path), paths)

        print(f"✓ Built language library: {lib_path}")
        print(f"\nLanguage library size: {lib_path.stat().st_size / 1024:.1f} KB")

        # Test loading
        print("\nStep 3: Testing language parsers...\n")

        for lang_name in ['python', 'javascript', 'typescript']:
            try:
                Language(str(lib_path), lang_name)
                print(f"✓ {lang_name} parser loaded successfully")
            except Exception as e:
                print(f"✗ Failed to load {lang_name} parser: {e}")
                return False

        print("\n" + "="*60)
        print("✓ Build complete! Language parsers ready.")
        print("="*60)
        return True

    except ImportError:
        print("✗ tree-sitter module not found. Install with: pip install tree-sitter")
        return False
    except Exception as e:
        print(f"✗ Build failed: {e}")
        return False


def clean():
    """Clean build artifacts"""
    script_dir = Path(__file__).parent
    vendor_dir = script_dir / 'vendor'
    build_dir = script_dir / 'build'

    print("Cleaning build artifacts...")

    if vendor_dir.exists():
        shutil.rmtree(vendor_dir)
        print(f"✓ Removed {vendor_dir}")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        print(f"✓ Removed {build_dir}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean()
        return

    success = build_languages()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
