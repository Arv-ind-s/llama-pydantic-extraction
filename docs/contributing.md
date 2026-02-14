# Contributing Guidelines

Thank you for your interest in contributing to **llama-pydantic-extraction**! This guide helps you get started.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/llama-pydantic-extraction.git
   cd llama-pydantic-extraction
   ```
3. **Set up** the development environment (see [Setup Guide](setup.md)).
4. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

---

## Development Workflow

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- Use type hints for all function signatures.
- Add docstrings (Google style) to all public functions and classes.
- Keep functions small and focused — one responsibility per function.
- Add inline comments only for non-obvious logic.

### Project Conventions

| Convention | Details |
|-----------|---------|
| Models | Pydantic v2 with `ConfigDict` (not `class Config`) |
| Async | Use `async/await` for I/O-bound operations |
| Logging | Use `get_logger(__name__)` from `src/utils/logger.py` |
| Settings | Access via `from config.settings import settings` |
| Error handling | Log and skip per-item; don't let one failure stop a batch |
| File I/O | Use helpers in `src/utils/file_utils.py` |

### Directory Rules

| Directory | Purpose | Notes |
|-----------|---------|-------|
| `src/schemas/` | Pydantic models | Field descriptions guide LLM extraction |
| `src/parsers/` | PDF parsing logic | LlamaCloud API calls |
| `src/extractors/` | LLM extraction + validation | Core pipeline logic |
| `src/utils/` | Shared helpers | Logging, file I/O |
| `config/` | Configuration | pydantic-settings based |
| `scripts/` | Standalone CLI tools | Must add `sys.path.insert` for imports |
| `tests/unit/` | Fast isolated tests | No API calls |
| `tests/integration/` | End-to-end tests | May require API key |

---

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add CSV export with custom delimiter
fix: handle empty answer_options in validation
docs: update API reference for new fields
refactor: extract diagram linking into standalone module
test: add unit tests for strip_code_fences
chore: update requirements.txt
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Unit tests only (fast, no API calls)
pytest tests/unit/

# Integration tests (requires LLAMA_CLOUD_API_KEY)
pytest tests/integration/

# With verbose output
pytest -v
```

### Writing Tests

- Place unit tests in `tests/unit/`.
- Place integration tests in `tests/integration/`.
- Name test files `test_<module>.py`.
- Test edge cases: empty input, invalid enums, missing fields, malformed JSON.

**Example unit test:**

```python
# tests/unit/test_question_schema.py
import pytest
from pydantic import ValidationError
from src.schemas.question_schema import Question, QuestionTags

def test_valid_question():
    q = Question(
        question_text="Test question?",
        answer_options={"A": "opt1", "B": "opt2", "C": "opt3", "D": "opt4"},
        correct_answer="A",
        language="English",
        category="History",
        tags=QuestionTags(difficulty="easy", topic="Test"),
        has_question_diagram=False,
        has_temporal_relevance=False,
        has_answer_diagrams=False,
    )
    assert q.correct_answer == "A"

def test_invalid_language_rejected():
    with pytest.raises(ValidationError):
        Question(
            question_text="Test?",
            answer_options={"A": "a"},
            correct_answer="A",
            language="Klingon",  # invalid
            category="History",
            tags=QuestionTags(difficulty="easy", topic="Test"),
            has_question_diagram=False,
            has_temporal_relevance=False,
            has_answer_diagrams=False,
        )
```

---

## Pull Request Process

1. Ensure your code passes all tests.
2. Update documentation if your changes affect public APIs or usage.
3. Keep PRs focused — one feature or fix per PR.
4. Write a clear PR description explaining:
   - **What** changed
   - **Why** the change was needed
   - **How** you tested it

---

## Adding a New Schema Field

If you need to add a field to the extraction schema:

1. Add the field to the appropriate model in `src/schemas/question_schema.py`.
2. Update `EXTRACTION_PROMPT` in `src/extractors/question_extractor.py` to include the new field.
3. Update `CSV_HEADERS` and `flatten_question()` in `scripts/export_csv.py` if the field should be exportable.
4. Update `docs/api_reference.md` with the new field documentation.
5. Add a test for the new field in `tests/unit/`.

---

## Questions?

Open an issue on GitHub or reach out to the maintainers.
