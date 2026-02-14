"""
Pydantic schema definitions for PSC (Public Service Commission) question extraction.

These models define the exact structure that LlamaParse should extract from
PSC question bank PDFs. Each field's `description` acts as an instruction
to the LLM during extraction — keep them clear and specific.

Models:
    - QuestionTags:           Categorisation & filtering metadata per question
    - Question:               A single MCQ with options, answer, and diagrams
    - DocumentMetadata:       PDF-level info (exam name, date, processing notes)
    - PSCQuestionExtraction:  Top-level wrapper — list of questions + metadata
"""

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Dict, List, Union
from enum import Enum


# ──────────────────────────────────────────────
# Enums — constrain values to known valid options
# ──────────────────────────────────────────────

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# 13 Indian & international languages commonly used in PSC exams
class Language(str, Enum):
    ENGLISH = "English"
    HINDI = "Hindi"
    MALAYALAM = "Malayalam"
    TAMIL = "Tamil"
    TELUGU = "Telugu"
    BENGALI = "Bengali"
    MARATHI = "Marathi"
    GUJARATI = "Gujarati"
    KANNADA = "Kannada"
    ODIA = "Odia"
    PUNJABI = "Punjabi"
    URDU = "Urdu"
    ASSAMESE = "Assamese"


# Subject categories covering the typical PSC exam syllabus
class Category(str, Enum):
    HISTORY = "History"
    CURRENT_AFFAIRS = "Current Affairs"
    GEOGRAPHY = "Geography"
    SCIENCE = "Science"
    POLITY = "Polity"
    ECONOMICS = "Economics"
    GENERAL_KNOWLEDGE = "General Knowledge"
    MATHEMATICS = "Mathematics"
    REASONING = "Reasoning"
    ENGLISH = "English"
    INDIAN_CULTURE = "Indian Culture"
    ENVIRONMENT = "Environment"
    TECHNOLOGY = "Technology"
    SPORTS = "Sports"
    ARTS_LITERATURE = "Arts & Literature"
    KERALA_STATE_AFFAIRS = "Kerala State Affairs"
    INDIAN_CONSTITUTION = "Indian Constitution"
    INTERNATIONAL_RELATIONS = "International Relations"


# ──────────────────────────────────────────────
# Nested models
# ──────────────────────────────────────────────

class QuestionTags(BaseModel):
    """Tagging metadata used for filtering, recommendation, and search."""

    difficulty: DifficultyLevel = Field(
        ..., 
        description="Difficulty level of the question"
    )
    topic: str = Field(
        ..., 
        description="Main topic of the question"
    )
    subtopic: Optional[str] = Field(
        None, 
        description="Specific subtopic within the main topic"
    )
    year_relevance: Optional[str] = Field(
        None, 
        description="Year of relevance for time-sensitive questions"
    )
    exam_type: Optional[str] = Field(
        None, 
        description="Type of exam"
    )
    importance: Optional[ImportanceLevel] = Field(
        None, 
        description="Importance level of the question"
    )
    keywords: List[str] = Field(
        default_factory=list, 
        description="Additional keyword tags"
    )


# ──────────────────────────────────────────────
# Core question model
# ──────────────────────────────────────────────

class Question(BaseModel):
    """
    Represents a single MCQ extracted from a PSC question bank PDF.

    Field descriptions are intentionally verbose — LlamaParse uses them
    as extraction instructions to guide the LLM.
    """

    # Serialize enums as their string values (e.g. "English" not Language.ENGLISH)
    model_config = ConfigDict(use_enum_values=True)

    # --- Core question content ---
    question_text: str = Field(
        ..., 
        description="The full text of the question"
    )
    answer_options: Dict[str, str] = Field(
        ..., 
        description="Dictionary mapping option keys (A, B, C, D, etc.) to option text"
    )
    correct_answer: str = Field(
        ..., 
        description="The correct option key from answer_options"
    )

    # --- Classification ---
    language: Language = Field(
        ..., 
        description="Language of the question"
    )
    category: Category = Field(
        ..., 
        description="Subject category of the question"
    )
    tags: QuestionTags = Field(
        ..., 
        description="Relevant tags for question recommendation and filtering"
    )

    # --- Diagram handling ---
    has_question_diagram: bool = Field(
        ..., 
        description="Indicates if the question includes a diagram"
    )
    question_diagram_path: Optional[str] = Field(
        None, 
        description="File path where the question diagram is saved"
    )
    has_answer_diagrams: bool = Field(
        ..., 
        description="Indicates if any answer option includes diagrams"
    )
    # Not Optional — defaults to empty dict; never None
    answer_diagram_paths: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping of option keys to their diagram file paths"
    )

    # --- Temporal flag ---
    has_temporal_relevance: bool = Field(
        ..., 
        description="Indicates if the answer could change over time"
    )

    # --- Optional metadata per question ---
    question_id: Optional[str] = Field(
        None, 
        description="Unique identifier for the question"
    )
    explanation: Optional[str] = Field(
        None, 
        description="Optional detailed explanation of the correct answer"
    )
    source: Optional[str] = Field(
        None, 
        description="Source reference for the question"
    )
    question_number: Optional[Union[int, str]] = Field(
        None, 
        description="Original question number from the PDF"
    )
    marks: Optional[float] = Field(
        None, 
        ge=0,  # marks can't be negative
        description="Marks allocated to this question"
    )
    negative_marking: Optional[bool] = Field(
        None, 
        description="Whether negative marking applies"
    )

    # --- Cross-field validators ---

    @model_validator(mode="after")
    def validate_correct_answer_in_options(self):
        """Reject if correct_answer isn't one of the answer_options keys."""
        if self.correct_answer not in self.answer_options:
            raise ValueError(
                f"correct_answer '{self.correct_answer}' is not a valid key "
                f"in answer_options {list(self.answer_options.keys())}"
            )
        return self

    @model_validator(mode="after")
    def validate_diagram_consistency(self):
        """Reject if diagram paths are provided but the diagram flag is False."""
        if not self.has_question_diagram and self.question_diagram_path is not None:
            raise ValueError(
                "question_diagram_path must be None when has_question_diagram is False"
            )
        if not self.has_answer_diagrams and self.answer_diagram_paths:
            raise ValueError(
                "answer_diagram_paths must be empty when has_answer_diagrams is False"
            )
        return self


# ──────────────────────────────────────────────
# Document-level metadata
# ──────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    """PDF-level metadata captured during extraction."""

    pdf_filename: Optional[str] = Field(
        None, 
        description="Original PDF filename"
    )
    # Stored as ISO 8601 string (not datetime) because LlamaParse returns strings
    extraction_date: Optional[str] = Field(
        None, 
        description="Timestamp of extraction as ISO 8601 string"
    )
    total_questions: Optional[int] = Field(
        None, 
        ge=0,
        description="Total number of questions extracted"
    )
    exam_name: Optional[str] = Field(
        None, 
        description="Name of the examination"
    )
    exam_date: Optional[str] = Field(
        None, 
        description="Date of the examination"
    )
    exam_year: Optional[int] = Field(
        None, 
        description="Year of the examination"
    )
    # Not Optional — defaults to empty list; never None
    processing_notes: List[str] = Field(
        default_factory=list, 
        description="Any notes or warnings during processing"
    )


# ──────────────────────────────────────────────
# Top-level extraction result
# ──────────────────────────────────────────────

class PSCQuestionExtraction(BaseModel):
    """
    Root model returned by the extraction pipeline.

    Pass this model to LlamaParse as the target schema — it will
    populate `questions` and `metadata` from the PDF content.
    """

    model_config = ConfigDict(use_enum_values=True)

    questions: List[Question] = Field(
        ..., 
        description="Array of extracted questions from the PDF"
    )
    metadata: Optional[DocumentMetadata] = Field(
        None, 
        description="Metadata about the PDF document"
    )