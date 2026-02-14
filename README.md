# llama-pydantic-extraction

Production-ready pipeline for extracting structured data from large PDF corpora. Combines LlamaCloud's intelligent parsing with Pydantic's type-safe validation to transform unstructured documents into validated Python objects at scale. Async processing, batch optimization, schema-driven extraction.

---

## Features

- **AI-Powered Parsing** — LlamaCloud handles complex PDF layouts, tables, and mixed content
- **Schema-Driven Extraction** — Define what you need with Pydantic models; get validated, typed output
- **Async & Batch Processing** — Process hundreds of PDFs concurrently with built-in rate limiting
- **Extensible Architecture** — Plug in custom extractors, parsers, and schemas for any document type
- **Robust Error Handling** — Retries, detailed logging, and graceful failure modes

## Project Structure

```
llama-pydantic-extraction/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── config/
│   └── settings.py                  # Centralised configuration & env loading
├── src/
│   ├── extractors/                  # LlamaCloud extraction logic
│   ├── parsers/                     # PDF parsing & content normalisation
│   ├── schemas/                     # Pydantic models for structured output
│   └── utils/                       # Shared helpers — logging, file I/O, async
├── scripts/                         # CLI scripts for batch ops & validation
├── data/
│   ├── input/                       # Place source PDFs here
│   └── output/                      # Validated JSON output lands here
├── tests/
│   ├── unit/                        # Fast, isolated unit tests
│   └── integration/                 # End-to-end pipeline tests
└── docs/                            # Additional documentation
```

## Getting Started

### Prerequisites

- Python 3.9+
- A [LlamaCloud API key](https://cloud.llamaindex.ai/)

### Installation

```bash
git clone https://github.com/Arv-ind-s/llama-pydantic-extraction.git
cd llama-pydantic-extraction
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

```env
LLAMA_CLOUD_API_KEY=llx-your-key-here
BATCH_SIZE=10
MAX_CONCURRENT_REQUESTS=5
```

Additional settings can be tuned in `config/settings.py`.

## Usage

Place your PDF files in the `data/input/` folder and run:

```bash
python main.py
```

Extracted, validated data will be written to `data/output/`.

## How It Works

```
PDF Files ──▶ LlamaCloud Parser ──▶ Raw JSON ──▶ Pydantic Validation ──▶ Structured Output
              (src/parsers)         (src/extractors)   (src/schemas)         (data/output)
```

1. **Parse** — PDFs are sent to LlamaCloud for intelligent content extraction
2. **Extract** — Raw parsed content is mapped to extraction targets
3. **Validate** — Pydantic models enforce types, constraints, and defaults
4. **Output** — Clean, validated JSON is written to `data/output/`

## Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m "feat: add my feature"`)
4. Push and open a Pull Request

## License

MIT