"""
Clean up temporary files and caches from the project directory.
This helps keep the repository clean and reduces its size.
"""
import os
import shutil
import argparse
from pathlib import Path

# Common temporary files and directories to clean
TEMP_PATTERNS = [
    # Python
    '__pycache__', '*.py[cod]', '*$py.class',
    '*.so', '.Python', 'build/', 'develop-eggs/', 'dist/',
    'downloads/', 'eggs/', '.eggs/', 'lib/', 'lib64/', 'parts/',
    'sdist/', 'var/', 'wheels/', '*.egg-info/', '.pytest_cache/',
    
    # Node.js
    'node_modules/', 'npm-debug.log*', 'yarn-debug.log*', 'yarn-error.log*',
    
    # IDEs and editors
    '.idea/', '.vscode/', '*.swp', '*.swo', '*.swn', '*.swo', '.DS_Store',
    'Thumbs.db', '*.sublime-workspace', '*.sublime-project',
    
    # Virtual environments
    '.venv/', 'venv/', 'ENV/', 'env/',
    
    # Build and distribution
    'build/', 'dist/', '*.egg-info/', '.eggs/',
    
    # Logs and databases
    '*.log', '*.sqlite', '*.db',
    
    # Jupyter
    '.ipynb_checkpoints',
    
    # Project specific
    'vector_store/', '.cache/'
]

# Files and directories to keep (won't be deleted)
KEEP_FILES = [
    '.git', '.gitignore', 'README.md', 'LICENSE', 'requirements.txt',
    'setup.py', 'config.json', 'config.example.json', 'run_app.py',
    'run_dev.py', 'setup.ps1', 'setup.sh', 'docs/', 'src/'
]

def clean_directory(directory, dry_run=False, patterns=None):
    """
    Clean up files and directories matching the given patterns.
    
    Args:
        directory: The directory to clean
        dry_run: If True, only show what would be deleted
        patterns: List of glob patterns to match files/directories to delete
    """
    if patterns is None:
        patterns = TEMP_PATTERNS
    
    # Convert to absolute paths
    directory = Path(directory).resolve()
    keep_paths = [directory / path for path in KEEP_FILES]
    
    print(f"🔍 Cleaning directory: {directory}")
    
    # Find all files and directories to delete
    to_delete = set()
    
    for pattern in patterns:
        # Handle directory patterns (ending with /)
        if pattern.endswith('/'):
            dir_pattern = pattern.rstrip('/')
            for path in directory.rglob(dir_pattern):
                if path.is_dir() and not any(is_relative_to(path, keep) for keep in keep_paths):
                    to_delete.add(path)
        else:
            for path in directory.rglob(pattern):
                if not any(is_relative_to(path, keep) for keep in keep_paths):
                    to_delete.add(path)
    
    # Sort paths for consistent output
    to_delete = sorted(to_delete, key=lambda p: (p.is_file(), str(p)))
    
    if not to_delete:
        print("✅ No files to clean up")
        return 0
    
    # Print what would be deleted
    print("\nThe following files/directories will be deleted:")
    for path in to_delete:
        if path.is_dir():
            print(f"  📁 {path.relative_to(directory)}/")
        else:
            print(f"  📄 {path.relative_to(directory)}")
    
    if dry_run:
        print("\n⚠️  Dry run completed. No files were deleted.")
        return 0
    
    # Ask for confirmation
    confirm = input(f"\n⚠️  Delete {len(to_delete)} files/directories? [y/N] ").strip().lower()
    if confirm != 'y':
        print("❌ Cleanup cancelled")
        return 1
    
    # Delete files and directories
    deleted_count = 0
    for path in to_delete:
        try:
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  🗑️  Deleted directory: {path.relative_to(directory)}/")
            else:
                path.unlink()
                print(f"  🗑️  Deleted file: {path.relative_to(directory)}")
            deleted_count += 1
        except Exception as e:
            print(f"  ❌ Error deleting {path.relative_to(directory)}: {e}")
    
    print(f"\n✅ Cleanup complete. Deleted {deleted_count} items.")
    return 0

def is_relative_to(path, base):
    """Check if a path is relative to a base path."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False

def main():
    """Parse command line arguments and run the cleaner."""
    parser = argparse.ArgumentParser(description='Clean up temporary files and caches')
    parser.add_argument('directory', nargs='?', default='.',
                       help='Directory to clean (default: current directory)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--patterns', nargs='+',
                       help='Additional file patterns to clean')
    
    args = parser.parse_args()
    
    # Combine default patterns with any additional patterns
    patterns = TEMP_PATTERNS.copy()
    if args.patterns:
        patterns.extend(args.patterns)
    
    return clean_directory(args.directory, args.dry_run, patterns)

if __name__ == '__main__':
    import sys
    sys.exit(main())
