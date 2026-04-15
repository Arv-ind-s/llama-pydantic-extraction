# Gemini CLI - Project Context: llama-pydantic-extraction

This document provides essential context and instructions for AI agents (like Gemini CLI) to understand and interact with the `llama-pydantic-extraction` codebase.

## Project Overview

A production-ready pipeline that transforms unstructured PDF question banks into validated, structured JSON data.

- **Purpose:** Automate the extraction of Multiple Choice Questions (MCQs) from complex PSC exam documents.
- **Core Stack:** Python 3.9+, [LlamaCloud](https://cloud.llamaindex.ai/) (Parsing & Inference), Pydantic v2 (Validation & Settings), `Asyncio` (Concurrency).
- **Key Features:**
    - **Agentic PDF Parsing:** Handles multi-column layouts, tables, and embedded images via LlamaCloud.
    - **Schema-Driven Extraction:** Uses Pydantic models to guide LLM extraction and ensure type safety.
    - **Diagram Linking:** Automatically matches downloaded PDF images to their corresponding questions.
    - **Graceful Validation:** Validates questions individually; invalid items are logged/skipped without failing the entire batch.

## Architecture & Data Flow

The pipeline follows a linear **Parse → Extract → Validate → Save** flow:

1.  **Parse (`src/parsers/`):** PDFs in `data/input/new/` are uploaded to LlamaCloud. Markdown and images are retrieved.
2.  **Extract (`src/extractors/`):** Markdown is sent to LlamaCloud's inference API (GPT-4o) with a schema-aware prompt.
3.  **Validate (`src/schemas/`):** Raw JSON is linked to local diagram paths and validated against Pydantic models.
4.  **Save (`src/utils/`):** Validated `PSCQuestionExtraction` objects are saved as timestamped JSON in `data/output/`.

## Key Files & Directories

- `main.py`: Entry point for the full async pipeline.
- `config/settings.py`: Centralized configuration using `pydantic-settings`.
- `src/schemas/question_schema.py`: Definitive Pydantic models for MCQs and metadata.
- `src/parsers/llama_parser.py`: LlamaCloud API integration for PDF parsing.
- `src/extractors/question_extractor.py`: LLM prompting, diagram linking, and validation logic.
- `scripts/`: CLI utilities for stats, CSV export, validation, and cleanup.
- `data/`:
    - `input/new/`: Source PDF drop zone.
    - `output/`: JSON results and `diagrams/` subfolder for extracted images.

## Development Workflows

### Setup & Configuration
1.  **Install dependencies:** `pip install -r requirements.txt`
2.  **Environment:** Create `.env` from `.env.example`. `LLAMA_CLOUD_API_KEY` is required.
3.  **Tuning:** Adjust `BATCH_SIZE` or `LOG_LEVEL` in `.env` or `config/settings.py`.

### Execution
- **Run pipeline:** `python main.py`
- **Reprocess specific files:** `python scripts/reprocess.py file1.pdf`
- **View statistics:** `python scripts/stats.py`
- **Export to CSV:** `python scripts/export_csv.py`

### Testing & Validation
- **Run all tests:** `pytest`
- **Validate existing output:** `python scripts/validate_output.py`

## Engineering Standards

- **Pydantic v2:** Use `model_dump()` and `ConfigDict`. Do not use V1 `dict()` or `class Config`.
- **Async First:** All I/O (API calls, file operations) must be `async`. Use `aiohttp` or `AsyncLlamaCloud`.
- **Enums for Metadata:** Use `(str, Enum)` for fixed fields like `Language`, `Category`, and `DifficultyLevel` to ensure clean JSON serialization.
- **Graceful Degradation:** When extracting collections, validate items individually so one malformed question doesn't discard the entire document.
- **Logging:** Use the factory in `src.utils.logger`. Favor `DEBUG` for extraction details and `WARNING` for validation errors.
