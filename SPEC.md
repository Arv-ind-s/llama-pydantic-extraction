# Project Specification: llama-pydantic-extraction

## 1. Overview
`llama-pydantic-extraction` is a production-ready pipeline designed to transform unstructured PDF question banks into validated, structured JSON data. It specifically targets Multiple Choice Questions (MCQs) from PSC (Public Service Commission) exam documents, which often feature complex layouts, multi-column text, and embedded diagrams.

### 1.1 Goals
- **High Fidelity Parsing:** Accurately extract text and structural elements from complex PDFs.
- **Schema-Driven Extraction:** Use LLMs guided by Pydantic models to ensure output consistency and type safety.
- **Diagram Integration:** Automatically download and link diagrams/images to their respective questions.
- **Robust Validation:** Validate extracted data at multiple levels (item-level and document-level).
- **Scalability:** Handle batches of documents concurrently with built-in retry logic.

### 1.2 Tech Stack
- **Language:** Python 3.9+
- **Parsing:** [LlamaCloud](https://cloud.llamaindex.ai/) (LlamaParse API)
- **Inference:** OpenAI GPT-4o (via LlamaCloud Inference API)
- **Validation:** Pydantic v2
- **Concurrency:** `asyncio`, `httpx`, `aiohttp`
- **Resilience:** `tenacity` for exponential backoff retries

---

## 2. Architecture

The pipeline follows a linear, asynchronous **Parse → Extract → Validate → Save** flow.

### 2.1 Pipeline Flow
1.  **Parse (`src/parsers/llama_parser.py`):**
    - Scans `data/input/new/` for PDFs.
    - Uploads PDFs to LlamaCloud.
    - Retrieves Markdown content and presigned URLs for embedded images.
    - Downloads images to `data/output/diagrams/<pdf_stem>/`.
2.  **Extract (`src/extractors/question_extractor.py`):**
    - Sends Markdown to the LLM with a schema-aware prompt.
    - Receives raw JSON representing the questions and metadata.
    - **Diagram Linking:** Uses regex to match downloaded image filenames to question numbers.
3.  **Validate (`src/schemas/question_schema.py`):**
    - Validates each question individually against the `Question` Pydantic model.
    - Collects valid questions into a `PSCQuestionExtraction` object.
    - Logs and skips individual questions that fail validation without failing the entire document.
4.  **Save (`src/utils/file_utils.py`):**
    - Serializes the validated `PSCQuestionExtraction` object to a timestamped JSON file in `data/output/`.

---

## 3. Data Models (Schemas)

The system relies on Pydantic v2 models defined in `src/schemas/question_schema.py`.

### 3.1 Enums
- `DifficultyLevel`: `easy`, `medium`, `hard`
- `ImportanceLevel`: `low`, `medium`, `high`, `critical`
- `Language`: English, Hindi, Malayalam, Tamil, etc.
- `Category`: History, Geography, Science, Polity, etc.

### 3.2 Core Models
- **`QuestionTags`**: Metadata for filtering (topic, subtopic, exam type, keywords).
- **`Question`**: Represents a single MCQ.
    - `question_text`: Full text.
    - `answer_options`: Dict (e.g., `{"A": "Option 1", ...}`).
    - `correct_answer`: The key of the correct option.
    - `has_question_diagram`: Boolean flag.
    - `question_diagram_path`: Local path to the linked image.
    - `tags`: Nested `QuestionTags` model.
- **`DocumentMetadata`**: PDF-level info (exam name, date, total questions, processing notes).
- **`PSCQuestionExtraction`**: Top-level container holding a list of `Question` objects and `DocumentMetadata`.

---

## 4. Components

### 4.1 `main.py`
The entry point that orchestrates the `AsyncLlamaCloud` client and the processing loop. It manages batching and final reporting.

### 4.2 `src/parsers/llama_parser.py`
- Integrates with LlamaCloud for "agentic" parsing.
- Handles file uploads and status polling.
- Extracts Markdown and image metadata.

### 4.3 `src/extractors/question_extractor.py`
- Contains the `EXTRACTION_PROMPT` which instructs the LLM on schema requirements.
- Performs "Surgical Validation": Iterates through LLM-returned questions and attempts to instantiate Pydantic models.
- **Linker Logic:** Matches images like `question_5.png` to the question with `question_number: 5`.

### 4.4 `src/utils/`
- `file_utils.py`: Async image downloading and JSON I/O.
- `logger.py`: Standardized logging with timestamps and module names.

### 4.5 `config/settings.py`
- Uses `pydantic-settings` to load configuration from environment variables or a `.env` file.
- Key settings: `llama_cloud_api_key`, `llm_model`, `batch_size`, `input_dir`, `output_dir`.

---

## 5. Directory Structure
```text
/
├── main.py                 # Pipeline entry point
├── config/
│   └── settings.py         # Configuration management
├── data/
│   ├── input/new/          # PDF drop zone
│   └── output/             # JSON results
│       └── diagrams/       # Extracted images subfolder
├── src/
│   ├── parsers/            # LlamaParse integration
│   ├── extractors/         # LLM logic & diagram linking
│   ├── schemas/            # Pydantic v2 models
│   └── utils/              # File I/O & Logging
└── scripts/                # CLI utilities (stats, export, etc.)
```

---

## 6. Resilience & Error Handling
- **Retries:** All API calls (LlamaCloud, LLM, Image Downloads) use `tenacity` with exponential backoff.
- **Validation Isolation:** A single malformed question in a 100-question PDF will be logged as a warning, but the other 99 valid questions will still be saved.
- **Batching:** The pipeline processes files in configurable batches (default 5) to balance speed and rate limits.

---

## 7. Operational Workflows
1.  **Setup:** Install requirements and configure `.env` with `LLAMA_CLOUD_API_KEY`.
2.  **Run:** Place PDFs in `data/input/new/` and execute `python main.py`.
3.  **Verify:** Check `data/output/` for JSON files and `data/output/diagrams/` for images.
4.  **Utilities:**
    - `scripts/stats.py`: Get a summary of processed questions.
    - `scripts/validate_output.py`: Re-validate saved JSON against the schema.
    - `scripts/export_csv.py`: Flatten JSON results for spreadsheet use.
