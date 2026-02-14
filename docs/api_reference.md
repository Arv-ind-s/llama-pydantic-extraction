# API Reference

Complete reference for all modules, classes, and functions in the codebase.

---

## Schemas — `src/schemas/question_schema.py`

### Enums

#### `DifficultyLevel`
Constrains question difficulty classification.

| Value | String |
|-------|--------|
| `EASY` | `"easy"` |
| `MEDIUM` | `"medium"` |
| `HARD` | `"hard"` |

#### `ImportanceLevel`
Rates question importance for exam preparation.

| Value | String |
|-------|--------|
| `LOW` | `"low"` |
| `MEDIUM` | `"medium"` |
| `HIGH` | `"high"` |
| `CRITICAL` | `"critical"` |

#### `Language`
Supported question languages. Values: `English`, `Hindi`, `Malayalam`, `Tamil`, `Telugu`, `Bengali`, `Marathi`, `Gujarati`, `Kannada`, `Odia`, `Punjabi`, `Urdu`, `Assamese`.

#### `Category`
Subject categories. Values: `History`, `Current Affairs`, `Geography`, `Science`, `Polity`, `Economics`, `General Knowledge`, `Mathematics`, `Reasoning`, `English`, `Indian Culture`, `Environment`, `Technology`, `Sports`, `Arts & Literature`, `Kerala State Affairs`, `Indian Constitution`, `International Relations`.

---

### Models

#### `QuestionTags`

Nested model for tagging, filtering, and recommendation metadata.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `difficulty` | `DifficultyLevel` | Yes | — | Difficulty level |
| `topic` | `str` | Yes | — | Main topic |
| `subtopic` | `Optional[str]` | No | `None` | Specific subtopic |
| `year_relevance` | `Optional[str]` | No | `None` | Year relevance for time-sensitive questions |
| `exam_type` | `Optional[str]` | No | `None` | Type of PSC exam |
| `importance` | `Optional[ImportanceLevel]` | No | `None` | Importance level |
| `keywords` | `List[str]` | No | `[]` | Keyword tags |

---

#### `Question`

Core model representing a single MCQ.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `question_text` | `str` | Yes | — | Full question text |
| `answer_options` | `Dict[str, str]` | Yes | — | Option keys mapped to text (e.g. `{"A": "...", "B": "..."}`) |
| `has_question_diagram` | `bool` | Yes | — | Whether question contains a diagram |
| `question_diagram_path` | `Optional[str]` | No | `None` | File path to question diagram |
| `language` | `Language` | Yes | — | Question language |
| `category` | `Category` | Yes | — | Subject category |
| `tags` | `QuestionTags` | Yes | — | Tagging metadata |
| `correct_answer` | `str` | Yes | — | Correct option key (e.g. `"A"`) |
| `has_temporal_relevance` | `bool` | Yes | — | Whether answer may change over time |
| `has_answer_diagrams` | `bool` | Yes | — | Whether answer options have diagrams |
| `answer_diagram_paths` | `Dict[str, str]` | No | `{}` | Option key → diagram path mapping |
| `question_id` | `Optional[str]` | No | `None` | Unique identifier |
| `explanation` | `Optional[str]` | No | `None` | Answer explanation |
| `source` | `Optional[str]` | No | `None` | Source reference |
| `question_number` | `Optional[Union[int, str]]` | No | `None` | Original question number |
| `marks` | `Optional[float]` | No | `None` | Allocated marks (≥ 0) |
| `negative_marking` | `Optional[bool]` | No | `None` | Whether negative marking applies |

**Config:** `use_enum_values=True` — enums serialize as strings in JSON output.

---

#### `DocumentMetadata`

PDF-level metadata captured during extraction.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `pdf_filename` | `Optional[str]` | No | `None` | Original PDF filename |
| `extraction_date` | `Optional[str]` | No | `None` | ISO 8601 timestamp (stored as string) |
| `total_questions` | `Optional[int]` | No | `None` | Count of extracted questions (≥ 0) |
| `exam_name` | `Optional[str]` | No | `None` | Examination name |
| `exam_date` | `Optional[str]` | No | `None` | Examination date |
| `exam_year` | `Optional[int]` | No | `None` | Examination year |
| `processing_notes` | `List[str]` | No | `[]` | Processing warnings and notes |

---

#### `PSCQuestionExtraction`

Top-level wrapper model. This is the target schema for the extraction pipeline.

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `questions` | `List[Question]` | Yes | — | Array of extracted questions |
| `metadata` | `Optional[DocumentMetadata]` | No | `None` | Document-level metadata |

---

## Parser — `src/parsers/llama_parser.py`

### Constants

| Name | Value | Description |
|------|-------|-------------|
| `NEW_PDF_DIR` | `settings.input_dir / "new"` | Directory scanned for input PDFs |

### Functions

#### `find_pdfs(directory: Path) → List[Path]`

Scan a directory for `.pdf` files.

| Parameter | Type | Description |
|-----------|------|-------------|
| `directory` | `Path` | Directory to scan |

**Returns:** Sorted list of PDF file paths. Empty list if directory doesn't exist.

---

#### `async parse_single_pdf(client: AsyncLlamaCloud, pdf_path: Path) → Dict`

Upload and parse a single PDF via LlamaCloud. Downloads embedded images.

| Parameter | Type | Description |
|-----------|------|-------------|
| `client` | `AsyncLlamaCloud` | Authenticated API client |
| `pdf_path` | `Path` | Path to the PDF file |

**Returns:** `{"filename": str, "markdown": str, "images": List[str]}`

---

#### `async parse_all_pdfs() → List[Dict]`

Main parsing entry point. Finds all PDFs in `data/input/new/` and parses each one.

**Returns:** List of parsed result dicts. Failed PDFs are logged and skipped.

---

## Extractor — `src/extractors/question_extractor.py`

### Constants

| Name | Description |
|------|-------------|
| `EXTRACTION_PROMPT` | Multi-line prompt template with full schema field descriptions and JSON example |

### Functions

#### `build_extraction_prompt(markdown_content: str) → str`

Appends document content to the extraction prompt template.

---

#### `async extract_with_llm(client, markdown_content: str) → Optional[Dict]`

Send markdown to LlamaCloud's inference API (GPT-4o) for structured extraction.

**Returns:** Parsed JSON dict, or `None` if extraction fails.

---

#### `strip_code_fences(text: str) → str`

Remove markdown code fences (`` ```json ... ``` ``) from LLM responses.

---

#### `link_diagram_paths(questions: List[Dict], image_paths: List[str], pdf_filename: str) → List[Dict]`

Match downloaded image files to questions based on filename patterns.

---

#### `validate_extraction(raw_data: Dict, pdf_filename: str) → Optional[PSCQuestionExtraction]`

Validate LLM output against the Pydantic schema. Validates each question individually — invalid questions are skipped, the rest are preserved.

**Returns:** Validated `PSCQuestionExtraction`, or `None` if all questions fail.

---

#### `async extract_from_parsed(client, parsed_result: Dict) → Optional[PSCQuestionExtraction]`

Full extraction pipeline: LLM → diagram linking → validation.

---

#### `async extract_and_save(client, parsed_result: Dict, output_dir: Path = None) → Optional[Path]`

Extract + save as timestamped JSON. Convenience wrapper around `extract_from_parsed()`.

**Returns:** Path to saved JSON file, or `None` if extraction failed.

---

## Utilities

### Logger — `src/utils/logger.py`

#### `get_logger(name: str) → logging.Logger`

Create a configured logger with console output. Log level is read from `settings.log_level`.

**Log format:** `2026-02-14 15:57:50 | INFO     | module.name | message`

Guards against duplicate handlers when called multiple times.

---

### File Utils — `src/utils/file_utils.py`

#### Constants

| Name | Value | Description |
|------|-------|-------------|
| `DIAGRAMS_DIR` | `settings.output_dir / "diagrams"` | Base directory for downloaded images |

#### `ensure_dir(directory: Path) → Path`

Create directory and parents if they don't exist. Returns the path for chaining.

#### `async download_image(url: str, save_path: Path) → bool`

Download an image from a presigned URL. Returns `True` on success, `False` on failure.

#### `save_json(data: Any, filename: str, output_dir: Path = None) → Path`

Serialize a dict or Pydantic model to a formatted JSON file. Auto-detects Pydantic models and calls `model_dump()`.

---

## Settings — `config/settings.py`

### `Settings(BaseSettings)`

Pydantic-settings model that loads configuration from `.env`.

```python
from config.settings import settings

settings.llama_cloud_api_key  # str (required)
settings.batch_size           # int, default 5
settings.max_retries          # int, default 3
settings.timeout              # int, default 300
settings.input_dir            # Path, default data/input
settings.output_dir           # Path, default data/output
settings.log_level            # str, default "INFO"
```

---

## Entry Point — `main.py`

### `async run_pipeline() → int`

Orchestrates the full pipeline. Returns the number of successfully processed PDFs.

### `main()`

Synchronous entry point. Runs `run_pipeline()` via `asyncio.run()`.

**Exit codes:**
| Code | Meaning |
|------|---------|
| `0` | At least one PDF processed |
| `1` | No PDFs processed or pipeline error |
| `130` | User interrupted (Ctrl+C) |
