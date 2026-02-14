"""
Clean up output files and downloaded diagrams.

Removes old extraction output and diagram files from data/output/.
Use --dry-run to preview what would be deleted without actually removing anything.

Usage:
    python scripts/clean_output.py              # delete all output
    python scripts/clean_output.py --dry-run    # preview only
    python scripts/clean_output.py --keep 5     # keep the 5 most recent files
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def get_output_files() -> list:
    """Get all JSON files in output directory, sorted oldest first."""
    output_dir = settings.output_dir
    if not output_dir.exists():
        return []
    return sorted(output_dir.glob("*.json"), key=lambda f: f.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description="Clean up output files and diagrams")
    parser.add_argument("--dry-run", action="store_true", help="Preview deletions without removing files")
    parser.add_argument("--keep", type=int, default=0, help="Number of most recent files to keep")
    parser.add_argument("--diagrams-only", action="store_true", help="Only clean diagram images, keep JSON")
    args = parser.parse_args()

    action = "Would delete" if args.dry_run else "Deleting"

    # Clean diagrams
    diagrams_dir = settings.output_dir / "diagrams"
    if diagrams_dir.exists() and not args.keep:
        size = sum(f.stat().st_size for f in diagrams_dir.rglob("*") if f.is_file())
        count = sum(1 for f in diagrams_dir.rglob("*") if f.is_file())
        print(f"{action} {count} diagram file(s) ({size / 1024:.1f} KB)")
        if not args.dry_run:
            shutil.rmtree(diagrams_dir)
            diagrams_dir.mkdir(exist_ok=True)

    if args.diagrams_only:
        print("Done (diagrams only).")
        return

    # Clean JSON output files
    files = get_output_files()

    if not files:
        print("No output files found.")
        return

    # Determine which files to delete
    if args.keep > 0:
        to_delete = files[:-args.keep] if len(files) > args.keep else []
        print(f"Keeping {args.keep} most recent file(s)")
    else:
        to_delete = files

    if not to_delete:
        print("Nothing to delete.")
        return

    for f in to_delete:
        print(f"  {action}: {f.name}")
        if not args.dry_run:
            f.unlink()

    print(f"\n{len(to_delete)} file(s) {'would be ' if args.dry_run else ''}deleted.")


if __name__ == "__main__":
    main()
