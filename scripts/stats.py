"""
Print statistics from extracted JSON output files.

Summarises question counts, category distribution, difficulty breakdown,
and language coverage across all output files.

Usage:
    python scripts/stats.py
    python scripts/stats.py --file data/output/specific_file.json
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def load_questions(filepath: Path) -> list:
    """Load questions from a JSON output file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("questions", [])


def print_stats(questions: list, label: str = "All Files"):
    """Print formatted statistics for a list of questions."""
    if not questions:
        print("No questions found.")
        return

    # Counters
    categories = Counter(q.get("category", "Unknown") for q in questions)
    difficulties = Counter(q.get("tags", {}).get("difficulty", "Unknown") for q in questions)
    languages = Counter(q.get("language", "Unknown") for q in questions)
    has_diagram = sum(1 for q in questions if q.get("has_question_diagram"))
    has_temporal = sum(1 for q in questions if q.get("has_temporal_relevance"))
    has_explanation = sum(1 for q in questions if q.get("explanation"))

    print(f"\n{'='*50}")
    print(f"  Statistics: {label}")
    print(f"{'='*50}")
    print(f"\n  Total questions: {len(questions)}")
    print(f"  With diagrams:   {has_diagram}")
    print(f"  With explanations: {has_explanation}")
    print(f"  Temporal (may change): {has_temporal}")

    print(f"\n  Categories:")
    for cat, count in categories.most_common():
        print(f"    {cat}: {count}")

    print(f"\n  Difficulty:")
    for diff, count in difficulties.most_common():
        print(f"    {diff}: {count}")

    print(f"\n  Languages:")
    for lang, count in languages.most_common():
        print(f"    {lang}: {count}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Show statistics from extraction output")
    parser.add_argument("--file", type=str, help="Analyse a specific JSON file")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(settings.output_dir.glob("*.json"))

    if not files:
        print("No JSON files found in output directory.")
        sys.exit(0)

    # Collect all questions across files
    all_questions = []
    for f in files:
        try:
            questions = load_questions(f)
            all_questions.extend(questions)
            if len(files) > 1:
                print_stats(questions, f.name)
        except Exception as e:
            print(f"  ✗ Error reading {f.name}: {e}")

    # Print combined stats if multiple files
    if len(files) > 1:
        print_stats(all_questions, "Combined")
    else:
        print_stats(all_questions, files[0].name)


if __name__ == "__main__":
    main()
