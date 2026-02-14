# Usage Examples

This guide covers common workflows with code snippets.

---

## 1. Basic Pipeline — Extract Questions from PDFs

Place PDFs in the input folder and run the pipeline:

```bash
# Place your PDFs
cp ~/Downloads/psc_2024_paper.pdf data/input/new/

# Run the pipeline
python main.py
```

**Expected output:**

```
2026-02-14 17:00:00 | INFO     | __main__ | ============================================================
2026-02-14 17:00:00 | INFO     | __main__ | PSC Question Extraction Pipeline — Starting
2026-02-14 17:00:00 | INFO     | __main__ | Input:  data/input/new
2026-02-14 17:00:00 | INFO     | __main__ | Output: data/output
2026-02-14 17:00:00 | INFO     | __main__ | ============================================================
2026-02-14 17:00:00 | INFO     | __main__ | [1/2] Parsing PDFs...
2026-02-14 17:00:05 | INFO     | src.parsers.llama_parser | Parsed psc_2024_paper.pdf successfully
2026-02-14 17:00:05 | INFO     | __main__ | [2/2] Extracting questions...
2026-02-14 17:00:15 | INFO     | src.extractors.question_extractor | Validated 50 question(s) from psc_2024_paper.pdf
2026-02-14 17:00:15 | INFO     | __main__ | ✓ Saved → data/output/psc_2024_paper_20260214_170015.json
2026-02-14 17:00:15 | INFO     | __main__ | Pipeline Complete
2026-02-14 17:00:15 | INFO     | __main__ |   Processed: 1/1 PDFs
2026-02-14 17:00:15 | INFO     | __main__ |   Time:      15.3s
```

---

## 2. Output JSON Structure

The pipeline produces JSON files like `data/output/psc_2024_paper_20260214_170015.json`:

```json
{
  "questions": [
    {
      "question_text": "Who was the first Prime Minister of India?",
      "answer_options": {
        "A": "Mahatma Gandhi",
        "B": "Jawaharlal Nehru",
        "C": "Sardar Patel",
        "D": "B.R. Ambedkar"
      },
      "has_question_diagram": false,
      "question_diagram_path": null,
      "language": "English",
      "category": "History",
      "tags": {
        "difficulty": "easy",
        "topic": "Indian Independence",
        "subtopic": "Post-independence Leaders",
        "year_relevance": "1947",
        "exam_type": null,
        "importance": "high",
        "keywords": ["prime minister", "independence", "nehru"]
      },
      "correct_answer": "B",
      "has_temporal_relevance": false,
      "has_answer_diagrams": false,
      "answer_diagram_paths": {},
      "question_id": null,
      "explanation": "Jawaharlal Nehru served as the first PM from 1947 to 1964.",
      "source": null,
      "question_number": 1,
      "marks": null,
      "negative_marking": null
    }
  ],
  "metadata": {
    "pdf_filename": "psc_2024_paper.pdf",
    "extraction_date": "2026-02-14T17:00:15.123456",
    "total_questions": 50,
    "exam_name": "Kerala PSC Preliminary Exam",
    "exam_date": null,
    "exam_year": 2024,
    "processing_notes": []
  }
}
```

---

## 3. CLI Utility Scripts

### Validate Output

Check that JSON files conform to the Pydantic schema:

```bash
# Validate all output files
python scripts/validate_output.py

# Validate a specific file
python scripts/validate_output.py --file data/output/psc_2024_paper_20260214_170015.json
```

### View Statistics

Get category, difficulty, and language breakdowns:

```bash
python scripts/stats.py
```

**Example output:**

```
==================================================
  Statistics: psc_2024_paper_20260214_170015.json
==================================================

  Total questions: 50
  With diagrams:   3
  With explanations: 45
  Temporal (may change): 2

  Categories:
    History: 12
    Current Affairs: 8
    Science: 7
    Geography: 6
    ...

  Difficulty:
    medium: 25
    easy: 15
    hard: 10

  Languages:
    English: 50
```

### Export to CSV

Convert JSON output to a flat CSV file for spreadsheets:

```bash
# Export all files
python scripts/export_csv.py

# Custom output filename
python scripts/export_csv.py --output my_questions.csv
```

### Clean Output

Remove old output files and diagrams:

```bash
# Preview what would be deleted
python scripts/clean_output.py --dry-run

# Delete everything
python scripts/clean_output.py

# Keep the 5 most recent files
python scripts/clean_output.py --keep 5

# Only clean diagram images
python scripts/clean_output.py --diagrams-only
```

### Reprocess Specific PDFs

Re-run the pipeline for PDFs that previously failed:

```bash
# Reprocess specific files
python scripts/reprocess.py psc_2024_paper.pdf psc_2023_paper.pdf

# Reprocess all PDFs
python scripts/reprocess.py --all
```

---

## 4. Using the Schema Programmatically

Import and use the Pydantic models directly in your own code:

```python
from src.schemas.question_schema import (
    PSCQuestionExtraction,
    Question,
    QuestionTags,
    DocumentMetadata,
)

# Create a question manually
question = Question(
    question_text="What is the capital of Kerala?",
    answer_options={"A": "Kochi", "B": "Thiruvananthapuram", "C": "Kozhikode", "D": "Thrissur"},
    correct_answer="B",
    language="English",
    category="Geography",
    tags=QuestionTags(difficulty="easy", topic="Indian States"),
    has_question_diagram=False,
    has_temporal_relevance=False,
    has_answer_diagrams=False,
)

# Validate and serialize
print(question.model_dump_json(indent=2))
```

---

## 5. Running the Parser Standalone

Test PDF parsing without the full pipeline:

```bash
python -m src.parsers.llama_parser
```

This parses all PDFs in `data/input/new/` and prints a preview of the markdown output.

---

## 6. Debug Logging

Enable verbose logging to troubleshoot issues:

```env
# In .env
LOG_LEVEL=DEBUG
```

This shows per-field validation errors, diagram linking details, and LLM response content.
