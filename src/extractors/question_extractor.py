"""
Question extractor for PSC question bank PDFs.

Takes raw markdown + image paths from the parser and uses an LLM
to extract structured question data validated against the
PSCQuestionExtraction Pydantic schema.

Flow:
    Parser output (markdown + images)
        → LLM structured extraction
        → Pydantic validation
        → Diagram path linking
        → PSCQuestionExtraction object
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError

from config.settings import settings
from src.schemas.question_schema import (
    PSCQuestionExtraction,
    Question,
    DocumentMetadata,
)
from src.utils.logger import get_logger
from src.utils.file_utils import save_json

logger = get_logger(__name__)


# --- Extraction prompt ---
# This prompt is sent to the LLM along with the parsed markdown content.
# It instructs the LLM to return structured JSON matching our schema.

EXTRACTION_PROMPT = """You are an expert at extracting structured data from PSC (Public Service Commission) question bank documents.

Given the following document content, extract ALL questions into a structured JSON format.

For EACH question, extract the following fields:
- question_text (required): The full text of the question
- answer_options (required): Dictionary mapping option keys (A, B, C, D) to their text
- has_question_diagram (required): true if the question references or contains a diagram/image, false otherwise
- question_diagram_path: null (will be populated later by the system)
- language (required): The language — one of: English, Hindi, Malayalam, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Odia, Punjabi, Urdu, Assamese
- category (required): Subject category — one of: History, Current Affairs, Geography, Science, Polity, Economics, General Knowledge, Mathematics, Reasoning, English, Indian Culture, Environment, Technology, Sports, Arts & Literature, Kerala State Affairs, Indian Constitution, International Relations
- tags (required): An object with:
    - difficulty (required): "easy", "medium", or "hard"
    - topic (required): Main topic of the question
    - subtopic: Specific subtopic within the main topic, or null
    - year_relevance: Year relevant to the question (e.g. "1947"), or null
    - exam_type: Type of PSC exam if identifiable, or null
    - importance: "low", "medium", "high", or "critical" — or null
    - keywords: List of keyword strings for tagging, or empty list []
- correct_answer (required): The correct option key (e.g. "A", "B", "C", "D")
- has_temporal_relevance (required): true if the answer could change over time (e.g. "Who is the current PM?"), false otherwise
- has_answer_diagrams (required): true if any answer option references a diagram/image, false otherwise
- answer_diagram_paths: empty object {} (will be populated later by the system)
- question_id: A unique identifier string, or null
- explanation: Explanation of the correct answer if provided in the document, or null
- source: Source reference for the question if mentioned, or null
- question_number: The original question number from the document (integer or string), or null
- marks: Marks allocated to this question (number >= 0), or null
- negative_marking: true/false if negative marking info is mentioned, or null

Also extract document-level metadata:
- exam_name: Name of the examination if mentioned, or null
- exam_date: Date of the exam if mentioned (as string), or null
- exam_year: Year of the exam if mentioned (as integer), or null
- total_questions: Total count of extracted questions

Return a JSON object with this exact structure:
{
    "questions": [
        {
            "question_text": "...",
            "answer_options": {"A": "...", "B": "...", "C": "...", "D": "..."},
            "has_question_diagram": false,
            "question_diagram_path": null,
            "language": "English",
            "category": "History",
            "tags": {
                "difficulty": "medium",
                "topic": "...",
                "subtopic": null,
                "year_relevance": null,
                "exam_type": null,
                "importance": null,
                "keywords": []
            },
            "correct_answer": "A",
            "has_temporal_relevance": false,
            "has_answer_diagrams": false,
            "answer_diagram_paths": {},
            "question_id": null,
            "explanation": null,
            "source": null,
            "question_number": 1,
            "marks": null,
            "negative_marking": null
        }
    ],
    "metadata": {
        "exam_name": null,
        "exam_date": null,
        "exam_year": null,
        "total_questions": 0
    }
}

IMPORTANT:
- Extract ALL questions from the document, do not skip any
- If the correct answer is not explicitly marked, set correct_answer to the best option
- Set has_temporal_relevance to true ONLY for questions whose answers may change over time
- Be accurate with category, difficulty, and language classification
- Leave question_diagram_path and answer_diagram_paths as null/{} — the system will link them
- Return ONLY valid JSON, no markdown fences, no explanatory text

Document content:
"""


def build_extraction_prompt(markdown_content: str) -> str:
    """
    Build the full prompt by appending document content to the extraction template.

    Args:
        markdown_content: Parsed markdown from LlamaParse.

    Returns:
        Complete prompt string for the LLM.
    """
    return EXTRACTION_PROMPT + markdown_content


async def extract_with_llm(client, markdown_content: str) -> Optional[Dict]:
    """
    Send parsed markdown to an LLM and get structured JSON back.

    Uses LlamaCloud's inference API to extract structured data
    from the document content.

    Args:
        client:           Authenticated AsyncLlamaCloud client.
        markdown_content: Raw markdown content from parser.

    Returns:
        Parsed JSON dict from LLM response, or None if extraction fails.
    """
    prompt = build_extraction_prompt(markdown_content)

    try:
        # Use LlamaCloud's inference endpoint for structured extraction
        response = await client.inference.chat(
            messages=[
                {"role": "system", "content": "You extract structured question data from PSC exam documents. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            model="gpt-4o",  # can be configured in settings later
        )

        # Extract the response text
        raw_text = response.choices[0].message.content.strip()

        # Clean up the response — LLMs sometimes wrap JSON in markdown code blocks
        raw_text = strip_code_fences(raw_text)

        return json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return None


def strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences (```json ... ```) that LLMs sometimes add.

    Args:
        text: Raw LLM response text.

    Returns:
        Clean JSON string.
    """
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def link_diagram_paths(
    questions: List[Dict],
    image_paths: List[str],
    pdf_filename: str,
) -> List[Dict]:
    """
    Match downloaded diagram paths to their corresponding questions.

    LlamaCloud saves images with filenames like 'page_1.jpg', 'image_1.png', etc.
    This function maps them to questions based on page/image references
    found in the markdown content.

    Args:
        questions:    List of question dicts from LLM extraction.
        image_paths:  List of local file paths to downloaded images.
        pdf_filename: Original PDF filename for logging.

    Returns:
        Updated questions list with diagram paths populated.
    """
    if not image_paths:
        return questions

    logger.info(f"Linking {len(image_paths)} image(s) to questions in {pdf_filename}")

    # Build a lookup of image filenames → full paths
    image_lookup = {Path(p).name: p for p in image_paths}

    for i, question in enumerate(questions):
        # If the question has a diagram flag but no path, try to find a matching image
        if question.get("has_question_diagram") and not question.get("question_diagram_path"):
            # Look for an image named after the question number or index
            q_num = question.get("question_number", i + 1)
            for img_name, img_path in image_lookup.items():
                if str(q_num) in img_name or f"question_{q_num}" in img_name.lower():
                    question["question_diagram_path"] = img_path
                    logger.debug(f"Linked diagram {img_name} → question {q_num}")
                    break

        # Same logic for answer diagrams
        if question.get("has_answer_diagrams") and not question.get("answer_diagram_paths"):
            answer_paths = {}
            for option_key in question.get("answer_options", {}).keys():
                for img_name, img_path in image_lookup.items():
                    if f"answer_{option_key}" in img_name.lower():
                        answer_paths[option_key] = img_path
                        break
            if answer_paths:
                question["answer_diagram_paths"] = answer_paths

    return questions


def validate_extraction(raw_data: Dict, pdf_filename: str) -> Optional[PSCQuestionExtraction]:
    """
    Validate raw LLM output against the PSCQuestionExtraction Pydantic schema.

    Handles common edge cases:
    - Missing optional fields (filled with defaults)
    - Invalid enum values (logged and skipped per-question)
    - Empty questions list (returns None)

    Args:
        raw_data:     Dict from LLM extraction.
        pdf_filename: PDF filename for metadata and logging.

    Returns:
        Validated PSCQuestionExtraction object, or None if validation fails entirely.
    """
    if not raw_data or "questions" not in raw_data:
        logger.error(f"No questions found in extraction output for {pdf_filename}")
        return None

    # Enrich metadata with processing info
    metadata = raw_data.get("metadata", {})
    metadata["pdf_filename"] = pdf_filename
    metadata["extraction_date"] = datetime.now().isoformat()
    metadata["total_questions"] = len(raw_data["questions"])

    # Validate questions one by one — skip invalid ones instead of failing the batch
    valid_questions = []
    processing_notes = []

    for i, q_data in enumerate(raw_data["questions"]):
        try:
            question = Question(**q_data)
            valid_questions.append(question)
        except ValidationError as e:
            q_num = q_data.get("question_number", i + 1)
            error_msg = f"Validation failed for question {q_num}: {e.error_count()} error(s)"
            logger.warning(error_msg)
            processing_notes.append(error_msg)

            # Log each specific validation error for debugging
            for error in e.errors():
                field = " → ".join(str(loc) for loc in error["loc"])
                logger.debug(f"  Field '{field}': {error['msg']}")

    if not valid_questions:
        logger.error(f"All questions failed validation for {pdf_filename}")
        return None

    # Update metadata with validation results
    metadata["total_questions"] = len(valid_questions)
    if processing_notes:
        metadata.setdefault("processing_notes", []).extend(processing_notes)

    skipped = len(raw_data["questions"]) - len(valid_questions)
    if skipped:
        logger.warning(f"{skipped} question(s) skipped due to validation errors in {pdf_filename}")

    # Build the final validated extraction object
    try:
        extraction = PSCQuestionExtraction(
            questions=valid_questions,
            metadata=DocumentMetadata(**metadata),
        )
        logger.info(
            f"Validated {len(valid_questions)} question(s) from {pdf_filename}"
        )
        return extraction
    except ValidationError as e:
        logger.error(f"Top-level validation failed for {pdf_filename}: {e}")
        return None


async def extract_from_parsed(
    client,
    parsed_result: Dict,
) -> Optional[PSCQuestionExtraction]:
    """
    Full extraction pipeline for a single parsed PDF.

    Steps:
        1. Send markdown to LLM for structured extraction
        2. Link downloaded diagram paths to questions
        3. Validate against Pydantic schema
        4. Return validated PSCQuestionExtraction

    Args:
        client:        Authenticated AsyncLlamaCloud client.
        parsed_result: Dict from parser with 'filename', 'markdown', 'images' keys.

    Returns:
        Validated PSCQuestionExtraction, or None if extraction fails.
    """
    filename = parsed_result["filename"]
    markdown = parsed_result["markdown"]
    images = parsed_result.get("images", [])

    logger.info(f"Starting extraction for {filename}")

    # Step 1: LLM structured extraction
    raw_data = await extract_with_llm(client, markdown)
    if raw_data is None:
        return None

    # Step 2: Link diagram paths to questions
    if images and "questions" in raw_data:
        raw_data["questions"] = link_diagram_paths(
            raw_data["questions"], images, filename
        )

    # Step 3: Validate and return
    return validate_extraction(raw_data, filename)


async def extract_and_save(
    client,
    parsed_result: Dict,
    output_dir: Path = None,
) -> Optional[Path]:
    """
    Extract questions from a parsed PDF and save the result as JSON.

    Convenience function that combines extraction + file output.

    Args:
        client:        Authenticated AsyncLlamaCloud client.
        parsed_result: Dict from parser with 'filename', 'markdown', 'images' keys.
        output_dir:    Where to save JSON. Defaults to settings.output_dir.

    Returns:
        Path to the saved JSON file, or None if extraction failed.
    """
    extraction = await extract_from_parsed(client, parsed_result)

    if extraction is None:
        logger.error(f"Extraction failed for {parsed_result['filename']} — no output saved")
        return None

    # Generate output filename: e.g. "psc_2024_20260214_163000.json"
    stem = Path(parsed_result["filename"]).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{stem}_{timestamp}.json"

    # Save the validated extraction as JSON
    filepath = save_json(extraction, output_filename, output_dir)
    return filepath
