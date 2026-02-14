# llama-pydantic-extraction

Production-ready pipeline for extracting structured data from large PDF corpora. Combines LlamaCloud's intelligent parsing with Pydantic's type-safe validation to transform unstructured documents into validated Python objects at scale. Async processing, batch optimization, schema-driven extraction.

## Usage

Place your PDF files in the `input/` folder and run:
```bash
python extract.py
```

The script will process all PDFs in the input directory and output structured data to the `output/` folder.