# Architecture & Design

## System Overview

The pipeline follows a linear **Parse → Extract → Validate → Save** architecture. Each stage is isolated into its own module with clear input/output contracts.

```
data/input/new/*.pdf
        │
        ▼
┌──────────────────────┐
│   llama_parser.py    │  Upload PDF → LlamaCloud → markdown + images
│   (src/parsers/)     │
└──────────┬───────────┘
           │  Dict: {filename, markdown, images}
           ▼
┌──────────────────────┐
│ question_extractor.py│  Markdown → LLM prompt → structured JSON
│  (src/extractors/)   │  → diagram linking → Pydantic validation
└──────────┬───────────┘
           │  PSCQuestionExtraction (validated)
           ▼
┌──────────────────────┐
│   file_utils.py      │  Save as timestamped JSON
│   (src/utils/)       │
└──────────┬───────────┘
           │
           ▼
   data/output/*.json
   data/output/diagrams/<pdf_name>/
```

## Component Breakdown

### 1. Configuration Layer

**File:** `config/settings.py`

A singleton `Settings` class built on `pydantic-settings`. Reads from `.env` at the project root and exposes typed configuration values:

| Setting | Type | Default |
|---------|------|---------|
| `llama_cloud_api_key` | `str` | *(required)* |
| `batch_size` | `int` | `5` |
| `max_retries` | `int` | `3` |
| `timeout` | `int` | `300` |
| `input_dir` | `Path` | `data/input` |
| `output_dir` | `Path` | `data/output` |
| `log_level` | `str` | `INFO` |

All values are overridable via environment variables.

---

### 2. Schema Layer

**File:** `src/schemas/question_schema.py`

Pydantic v2 models that define the target output structure. These serve a dual purpose:
1. **LLM Guidance** — Field descriptions are embedded in the extraction prompt to instruct the LLM.
2. **Output Validation** — Extracted data is validated against these models before saving.

**Model hierarchy:**

```
PSCQuestionExtraction
├── questions: List[Question]
│   ├── question_text, answer_options, correct_answer
│   ├── language (Language enum), category (Category enum)
│   ├── tags: QuestionTags
│   │   ├── difficulty (DifficultyLevel enum)
│   │   ├── topic, subtopic, year_relevance
│   │   ├── exam_type, importance (ImportanceLevel enum)
│   │   └── keywords: List[str]
│   ├── has_question_diagram, question_diagram_path
│   ├── has_answer_diagrams, answer_diagram_paths
│   ├── has_temporal_relevance
│   ├── question_id, explanation, source
│   ├── question_number, marks, negative_marking
│   └── model_config: ConfigDict(use_enum_values=True)
└── metadata: DocumentMetadata
    ├── pdf_filename, extraction_date (str)
    ├── total_questions, exam_name, exam_date, exam_year
    └── processing_notes: List[str]
```

**Enums:** `DifficultyLevel`, `ImportanceLevel`, `Language`, `Category` — all inherit from `(str, Enum)` for clean JSON serialization.

---

### 3. Parser Layer

**File:** `src/parsers/llama_parser.py`

Handles all communication with the LlamaCloud API:

1. **`find_pdfs(directory)`** — Scans for `.pdf` files in the specified directory.
2. **`parse_single_pdf(client, pdf_path)`** — Uploads a PDF, requests parsing with the `agentic` tier, collects markdown content across all pages, and downloads any embedded images/diagrams.
3. **`parse_all_pdfs()`** — Iterates over all PDFs in `data/input/new/` with per-file error isolation.

**Key design decisions:**
- Uses `AsyncLlamaCloud` for non-blocking I/O.
- Requests `expand=["markdown", "images_content_metadata"]` to get both content and image URLs.
- Images are saved to `data/output/diagrams/<pdf_stem>/` for per-document organisation.
- One failed PDF does not stop the batch.

---

### 4. Extractor Layer

**File:** `src/extractors/question_extractor.py`

The core intelligence of the pipeline:

1. **`build_extraction_prompt(markdown)`** — Constructs a detailed prompt listing every schema field with types, constraints, and a full JSON example.
2. **`extract_with_llm(client, markdown)`** — Sends the prompt to LlamaCloud's inference API (GPT-4o) and parses the JSON response.
3. **`strip_code_fences(text)`** — Cleans markdown code fences that LLMs sometimes wrap around JSON.
4. **`link_diagram_paths(questions, images, filename)`** — Matches downloaded image files to questions by filename pattern matching.
5. **`validate_extraction(raw_data, filename)`** — Per-question Pydantic validation with graceful degradation (invalid questions are skipped, not fatal).
6. **`extract_from_parsed(client, parsed_result)`** — Full pipeline: LLM → link diagrams → validate.
7. **`extract_and_save(client, parsed_result)`** — Pipeline + save to disk.

**Error handling strategy:**
- Invalid JSON from LLM → logged, returns `None`
- Per-question validation failure → question skipped, rest preserved
- All questions invalid → returns `None`, no file written
- Processing notes track all skipped questions for audit

---

### 5. Utilities Layer

**Files:** `src/utils/logger.py`, `src/utils/file_utils.py`

| Module | Functions | Purpose |
|--------|-----------|---------|
| `logger.py` | `get_logger(name)` | Factory for configured loggers with console output and settings-driven log level |
| `file_utils.py` | `ensure_dir(path)` | Create directories safely |
| | `download_image(url, path)` | Async download from presigned URLs |
| | `save_json(data, filename)` | Serialize dicts or Pydantic models to formatted JSON |

---

### 6. Entry Point

**File:** `main.py`

Orchestrates the two-phase pipeline:
1. **Phase 1:** Parse all PDFs (calls `parse_all_pdfs()`)
2. **Phase 2:** Extract + validate + save each result (calls `extract_and_save()` per PDF)

Provides timing, progress logging, and proper exit codes (`0` = success, `1` = failure, `130` = user interrupt).

---

## Data Flow

```
[PDF File] ──upload──▶ [LlamaCloud API]
                            │
                    parse (agentic tier)
                            │
                   ┌────────┴────────┐
                   │                 │
              [Markdown]     [Image URLs]
                   │                 │
                   │          async download
                   │                 │
                   │        [Local Image Files]
                   │                 │
                   └────────┬────────┘
                            │
              {filename, markdown, images}
                            │
                   ┌────────┴────────┐
                   │  LLM Inference  │
                   │   (GPT-4o)      │
                   └────────┬────────┘
                            │
                     [Raw JSON Dict]
                            │
                   ┌────────┴────────┐
                   │ Link Diagrams   │
                   │ to Questions    │
                   └────────┬────────┘
                            │
                   ┌────────┴────────┐
                   │ Pydantic        │
                   │ Validation      │
                   │ (per question)  │
                   └────────┬────────┘
                            │
              [PSCQuestionExtraction]
                            │
                      save_json()
                            │
              [data/output/<name>_<ts>.json]
```

## Directory Structure

```
llama-pydantic-extraction/
├── main.py                          # Pipeline entry point
├── requirements.txt                 # Python dependencies
├── .env                             # API keys (gitignored)
├── .env.example                     # Template for .env
├── config/
│   └── settings.py                  # Centralised configuration
├── src/
│   ├── extractors/
│   │   └── question_extractor.py    # LLM extraction + validation
│   ├── parsers/
│   │   └── llama_parser.py          # LlamaCloud PDF parsing
│   ├── schemas/
│   │   └── question_schema.py       # Pydantic models
│   └── utils/
│       ├── logger.py                # Logging factory
│       └── file_utils.py            # File I/O helpers
├── scripts/
│   ├── validate_output.py           # Schema validation check
│   ├── stats.py                     # Output statistics
│   ├── export_csv.py                # JSON → CSV export
│   ├── clean_output.py              # Cleanup utility
│   └── reprocess.py                 # Selective reprocessing
├── data/
│   ├── input/new/                   # Place source PDFs here
│   └── output/                      # Validated JSON output
│       └── diagrams/                # Downloaded images
├── tests/
│   ├── unit/
│   └── integration/
└── docs/                            # This documentation
```
