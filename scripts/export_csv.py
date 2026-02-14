"""
Export extracted JSON output to CSV format.

Flattens the nested question structure into a flat CSV row
for use in spreadsheets or data analysis tools.

Usage:
    python scripts/export_csv.py
    python scripts/export_csv.py --file data/output/specific_file.json
    python scripts/export_csv.py --output exported_questions.csv
"""
import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


# CSV column headers — flattened from the nested JSON structure
CSV_HEADERS = [
    "source_file",
    "question_number",
    "question_text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "language",
    "category",
    "difficulty",
    "topic",
    "subtopic",
    "has_question_diagram",
    "has_answer_diagrams",
    "has_temporal_relevance",
    "explanation",
    "marks",
    "negative_marking",
    "keywords",
]


def flatten_question(question: dict, source_file: str) -> dict:
    """
    Flatten a nested question dict into a single-level row for CSV.

    Args:
        question:    Nested question dict from JSON output.
        source_file: Name of the source JSON file.

    Returns:
        Flat dict matching CSV_HEADERS.
    """
    options = question.get("answer_options", {})
    tags = question.get("tags", {})

    return {
        "source_file": source_file,
        "question_number": question.get("question_number", ""),
        "question_text": question.get("question_text", ""),
        "option_a": options.get("A", ""),
        "option_b": options.get("B", ""),
        "option_c": options.get("C", ""),
        "option_d": options.get("D", ""),
        "correct_answer": question.get("correct_answer", ""),
        "language": question.get("language", ""),
        "category": question.get("category", ""),
        "difficulty": tags.get("difficulty", ""),
        "topic": tags.get("topic", ""),
        "subtopic": tags.get("subtopic", ""),
        "has_question_diagram": question.get("has_question_diagram", False),
        "has_answer_diagrams": question.get("has_answer_diagrams", False),
        "has_temporal_relevance": question.get("has_temporal_relevance", False),
        "explanation": question.get("explanation", ""),
        "marks": question.get("marks", ""),
        "negative_marking": question.get("negative_marking", ""),
        "keywords": ", ".join(tags.get("keywords", [])),
    }


def main():
    parser = argparse.ArgumentParser(description="Export extraction output to CSV")
    parser.add_argument("--file", type=str, help="Export a specific JSON file")
    parser.add_argument("--output", type=str, default="questions_export.csv", help="Output CSV filename")
    args = parser.parse_args()

    if args.file:
        files = [Path(args.file)]
    else:
        files = sorted(settings.output_dir.glob("*.json"))

    if not files:
        print("No JSON files found to export.")
        sys.exit(0)

    # Collect all rows
    rows = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            for q in data.get("questions", []):
                rows.append(flatten_question(q, f.name))
        except Exception as e:
            print(f"  ✗ Error reading {f.name}: {e}")

    if not rows:
        print("No questions found to export.")
        sys.exit(0)

    # Write CSV
    output_path = settings.output_dir / args.output
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} question(s) → {output_path}")


if __name__ == "__main__":
    main()
