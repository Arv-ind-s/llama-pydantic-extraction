# Project Overview

## What is llama-pydantic-extraction?

**llama-pydantic-extraction** is a Python pipeline for extracting structured multiple-choice question (MCQ) data from PSC (Public Service Commission) question bank PDFs. It combines LlamaCloud's AI-powered document parsing with Pydantic's type-safe schema validation to transform unstructured PDFs into clean, validated JSON output.

## Problem Statement

PSC question banks are distributed as PDF documents containing hundreds of MCQs in varying formats, languages, and layouts. Manually digitising these into structured databases is time-consuming and error-prone. This project automates the entire process.

## Key Features

| Feature | Description |
|---------|-------------|
| **AI-Powered Parsing** | LlamaCloud handles complex PDF layouts, tables, diagrams, and mixed-language content |
| **Schema-Driven Extraction** | Pydantic models define the exact output structure; the LLM is prompted to match it |
| **Diagram Handling** | Automatically downloads images/diagrams from parsed PDFs and links them to questions |
| **Per-Question Validation** | Invalid questions are skipped individually — one bad question doesn't fail the batch |
| **Batch Processing** | Processes multiple PDFs in sequence with per-file error isolation |
| **CLI Utilities** | Scripts for validation, statistics, CSV export, cleanup, and selective reprocessing |

## Supported Languages

English, Hindi, Malayalam, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Odia, Punjabi, Urdu, and Assamese.

## Supported Categories

History, Current Affairs, Geography, Science, Polity, Economics, General Knowledge, Mathematics, Reasoning, English, Indian Culture, Environment, Technology, Sports, Arts & Literature, Kerala State Affairs, Indian Constitution, and International Relations.

## Technology Stack

| Component | Technology |
|-----------|------------|
| PDF Parsing | LlamaCloud SDK (`llama-cloud`) |
| LLM Extraction | LlamaCloud Inference API (GPT-4o) |
| Schema Validation | Pydantic v2 |
| Configuration | pydantic-settings + `.env` |
| Async I/O | asyncio, httpx, aiohttp |
| Image Downloads | httpx (async) |
| Logging | Python `logging` module |
| Testing | pytest, pytest-asyncio |

## Output Format

Each processed PDF produces a timestamped JSON file containing:
- An array of validated `Question` objects (with text, options, correct answer, category, tags, diagram paths, etc.)
- A `DocumentMetadata` object (PDF filename, exam info, extraction timestamp, processing notes)

See [API Reference](api_reference.md) for the full schema specification.
