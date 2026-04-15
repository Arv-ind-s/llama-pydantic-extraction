"""
Question extractor for PSC question bank PDFs.

Takes raw markdown + image paths from the parser and uses an LLM
to extract structured question data validated against the
PSCQuestionExtraction Pydantic schema.
"""
import json
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

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
    return EXTRACTION_PROMPT + markdown_content


@retry(
    stop=stop_after_attempt(settings.max_retries),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((asyncio.TimeoutError, Exception)),
)
async def extract_with_llm(client, markdown_content: str) -> Optional[Dict]:
    """
    Send parsed markdown to an LLM and get structured JSON back.
    Includes retry logic for reliability.
    """
    prompt = build_extraction_prompt(markdown_content)

    try:
        response = await client.inference.chat(
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured question data from PSC exam documents. Always respond with valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            model=settings.llm_model,
        )

        raw_text = response.choices[0].message.content.strip()
        raw_text = strip_code_fences(raw_text)

        return json.loads(raw_text)

    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise  # tenacity will catch this and retry


def strip_code_fences(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def link_diagram_paths(
    questions: List[Dict],
    image_paths: List[str],
    pdf_filename: str,
) -> List[Dict]:
    """
    Match downloaded diagram paths to their corresponding questions using regex.
    Prevents false positives (e.g. Q1 matching image_11.png).
    """
    if not image_paths:
        return questions

    logger.info(f"Linking {len(image_paths)} image(s) to questions in {pdf_filename}")

    image_lookup = {Path(p).name: p for p in image_paths}

    for i, question in enumerate(questions):
        q_num = str(question.get("question_number", i + 1))
        
        # Regex to match exact question number in filename
        # Matches "question_1.png", "q1.jpg", "page_1_image_1.png", but NOT "question_11.png"
        q_pattern = re.compile(fr"(?:^|[^0-9]){re.escape(q_num)}(?:[^0-9]|$)", re.IGNORECASE)

        if question.get("has_question_diagram") and not question.get("question_diagram_path"):
            for img_name, img_path in image_lookup.items():
                if q_pattern.search(img_name) or f"question_{q_num}" in img_name.lower():
                    question["question_diagram_path"] = img_path
                    logger.debug(f"Linked diagram {img_name} → question {q_num}")
                    break

        if question.get("has_answer_diagrams") and not question.get("answer_diagram_paths"):
            answer_paths = {}
            for option_key in question.get("answer_options", {}).keys():
                # Pattern for answer specific diagrams e.g. "q1_a.png" or "ans_A_1.jpg"
                a_pattern = re.compile(fr"ans(?:wer)?_{option_key}", re.IGNORECASE)
                for img_name, img_path in image_lookup.items():
                    if q_pattern.search(img_name) and a_pattern.search(img_name):
                        answer_paths[option_key] = img_path
                        break
            if answer_paths:
                question["answer_diagram_paths"] = answer_paths

    return questions


def validate_extraction(raw_data: Dict, pdf_filename: str) -> Optional[PSCQuestionExtraction]:
    if not raw_data or "questions" not in raw_data:
        logger.error(f"No questions found in extraction output for {pdf_filename}")
        return None

    metadata = raw_data.get("metadata", {})
    metadata["pdf_filename"] = pdf_filename
    metadata["extraction_date"] = datetime.now().isoformat()
    metadata["total_questions"] = len(raw_data["questions"])

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

            for error in e.errors():
                field = " → ".join(str(loc) for loc in error["loc"])
                logger.debug(f"  Field '{field}': {error['msg']}")

    if not valid_questions:
        logger.error(f"All questions failed validation for {pdf_filename}")
        return None

    metadata["total_questions"] = len(valid_questions)
    if processing_notes:
        metadata.setdefault("processing_notes", []).extend(processing_notes)

    try:
        extraction = PSCQuestionExtraction(
            questions=valid_questions,
            metadata=DocumentMetadata(**metadata),
        )
        logger.info(f"Validated {len(valid_questions)} question(s) from {pdf_filename}")
        return extraction
    except ValidationError as e:
        logger.error(f"Top-level validation failed for {pdf_filename}: {e}")
        return None


async def extract_from_parsed(client, parsed_result: Dict) -> Optional[PSCQuestionExtraction]:
    filename = parsed_result["filename"]
    markdown = parsed_result["markdown"]
    images = parsed_result.get("images", [])

    logger.info(f"Starting extraction for {filename}")

    raw_data = await extract_with_llm(client, markdown)
    if raw_data is None:
        return None

    if images and "questions" in raw_data:
        raw_data["questions"] = link_diagram_paths(raw_data["questions"], images, filename)

    return validate_extraction(raw_data, filename)


async def extract_and_save(client, parsed_result: Dict, output_dir: Path = None) -> Optional[Path]:
    try:
        extraction = await extract_from_parsed(client, parsed_result)
        if extraction is None:
            return None

        stem = Path(parsed_result["filename"]).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{stem}_{timestamp}.json"

        return save_json(extraction, output_filename, output_dir)
    except Exception as e:
        logger.error(f"Failed to process extraction for {parsed_result['filename']}: {e}")
        return None
