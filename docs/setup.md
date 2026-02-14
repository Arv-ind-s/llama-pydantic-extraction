# Installation & Setup

## Prerequisites

- **Python 3.9+**
- **pip** (package manager)
- A [LlamaCloud API key](https://cloud.llamaindex.ai/)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Arv-ind-s/llama-pydantic-extraction.git
cd llama-pydantic-extraction
```

## Step 2: Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Dependency Overview

| Package | Version | Purpose |
|---------|---------|---------|
| `llama-cloud` | ≥ 1.0 | LlamaCloud SDK for PDF parsing and LLM inference |
| `pydantic` | ≥ 2.0 | Data validation and schema definition |
| `pydantic-settings` | ≥ 2.0 | Configuration management from `.env` files |
| `aiohttp` | ≥ 3.9 | Async HTTP client |
| `aiofiles` | ≥ 23.0 | Async file operations |
| `httpx` | — | Async image downloads |
| `python-dotenv` | ≥ 1.0 | `.env` file loading |
| `tqdm` | ≥ 4.66 | Progress bars |
| `tenacity` | ≥ 8.2 | Retry logic for API calls |
| `pytest` | ≥ 7.0 | Test framework |
| `pytest-asyncio` | ≥ 0.23 | Async test support |

## Step 4: Configure Environment

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Required
LLAMA_CLOUD_API_KEY=llx-your-actual-api-key

# Optional (defaults shown)
BATCH_SIZE=5
MAX_RETRIES=3
TIMEOUT=300
LOG_LEVEL=INFO
```

> **Note:** The `.env` file is gitignored. Never commit API keys to version control.

### Configuration Reference

All settings are defined in `config/settings.py` and can be overridden via environment variables:

| Environment Variable | Type | Default | Required |
|---------------------|------|---------|----------|
| `LLAMA_CLOUD_API_KEY` | string | — | **Yes** |
| `BATCH_SIZE` | int | `5` | No |
| `MAX_RETRIES` | int | `3` | No |
| `TIMEOUT` | int | `300` (seconds) | No |
| `INPUT_DIR` | path | `data/input` | No |
| `OUTPUT_DIR` | path | `data/output` | No |
| `LOG_LEVEL` | string | `INFO` | No |

## Step 5: Verify Setup

```bash
# Check that imports work
python -c "from config.settings import settings; print('Settings loaded:', settings.log_level)"

# Check the schema loads
python -c "from src.schemas.question_schema import PSCQuestionExtraction; print('Schema OK')"
```

## Directory Preparation

Ensure the input directory for new PDFs exists:

```bash
mkdir -p data/input/new
```

Place your PDF files in `data/input/new/` before running the pipeline.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pydantic_settings` | Run `pip install pydantic-settings` |
| `ValidationError` on startup | Check that `LLAMA_CLOUD_API_KEY` is set in `.env` |
| `ConnectionError` during parsing | Verify your API key is valid at [cloud.llamaindex.ai](https://cloud.llamaindex.ai/) |
| Permission errors on `data/output/` | Ensure the directory is writable: `chmod -R 755 data/` |
