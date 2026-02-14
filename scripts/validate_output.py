"""
Validate existing JSON output files against the Pydantic schema.

Scans data/output/ for JSON files and checks each one against
PSCQuestionExtraction. Reports valid/invalid files and error details.

Usage:
    python scripts/validate_output.py
    python scripts/validate_output.py --file data/output/specific_file.json
"""
import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

# Add project root to path so imports work when running as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from src.schemas.question_schema import PSCQuestionExtraction


def validate_file(filepath: Path) -> bool:
    """
    Validate a single JSON file against the schema.

    Returns True if valid, False otherwise.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        extraction = PSCQuestionExtraction(**data)
        print(f"  ✓ {filepath.name} — {len(extraction.questions)} question(s)")
        return True

    except json.JSONDecodeError as e:
        print(f"  ✗ {filepath.name} — Invalid JSON: {e}")
        return False

    except ValidationError as e:
        print(f"  ✗ {filepath.name} — {e.error_count()} validation error(s):")
        for error in e.errors():
            field = " → ".join(str(loc) for loc in error["loc"])
            print(f"      {field}: {error['msg']}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Validate extraction output against the schema")
    parser.add_argument("--file", type=str, help="Validate a specific JSON file")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        output_dir = settings.output_dir
        files = sorted(output_dir.glob("*.json"))

    if not files:
        print("No JSON files found to validate.")
        sys.exit(0)

    print(f"Validating {len(files)} file(s)...\n")

    valid = sum(1 for f in files if validate_file(f))
    invalid = len(files) - valid

    print(f"\nResults: {valid} valid, {invalid} invalid out of {len(files)} file(s)")
    sys.exit(0 if invalid == 0 else 1)


if __name__ == "__main__":
    main()
