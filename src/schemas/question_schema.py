"""
Pydantic models for PSC Question Extraction.

Defines the target schema for extracting structured MCQ data from
PSC (Public Service Commission) question bank PDFs via LlamaParse.
Field descriptions guide the LLM during extraction.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, List, Union
from enum import Enum

# --- Enums: constrain extracted values to known valid options ---

class DifficultyLevel(str, Enum):  # str mixin allows JSON serialization as strings
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ImportanceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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

# --- Nested model for tagging/filtering metadata ---

class QuestionTags(BaseModel):
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
        description="Type of PSC exam"
    )
    importance: Optional[ImportanceLevel] = Field(
        None, 
        description="Importance level of the question"
    )
    keywords: List[str] = Field(
        default_factory=list, 
        description="Additional keyword tags"
    )

# --- Core model: a single MCQ extracted from a PDF ---

class Question(BaseModel):
    question_text: str = Field(
        ..., 
        description="The full text of the question"
    )
    answer_options: Dict[str, str] = Field(
        ..., 
        description="Dictionary mapping option keys (A, B, C, D, etc.) to option text"
    )
    has_question_diagram: bool = Field(
        ..., 
        description="Indicates if the question includes a diagram"
    )
    question_diagram_path: Optional[str] = Field(
        None, 
        description="File path where the question diagram is saved"
    )
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
    correct_answer: str = Field(
        ..., 
        description="The correct option key from answer_options"
    )
    has_temporal_relevance: bool = Field(
        ..., 
        description="Indicates if the answer could change over time"
    )
    has_answer_diagrams: bool = Field(
        ..., 
        description="Indicates if any answer option includes diagrams"
    )
    answer_diagram_paths: Dict[str, str] = Field(  # defaults to {} via factory, never None
        default_factory=dict, 
        description="Mapping of option keys to their diagram file paths"
    )
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
    question_number: Optional[Union[int, str]] = Field(  # Union handles PDFs with numeric or alphanumeric numbering
        None, 
        description="Original question number from the PDF"
    )
    marks: Optional[float] = Field(
        None, 
        ge=0,
        description="Marks allocated to this question"
    )
    negative_marking: Optional[bool] = Field(
        None, 
        description="Whether negative marking applies"
    )

    # Serialize enums as their string values (e.g. "English" instead of Language.ENGLISH)
    model_config = ConfigDict(use_enum_values=True)

# --- PDF-level metadata captured during extraction ---

class DocumentMetadata(BaseModel):
    pdf_filename: Optional[str] = Field(
        None, 
        description="Original PDF filename"
    )
    extraction_date: Optional[str] = Field(  # str, not datetime — LlamaParse returns strings
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
    processing_notes: List[str] = Field(
        default_factory=list, 
        description="Any notes or warnings during processing"
    )

# --- Top-level wrapper: pass this to LlamaParse as the target schema ---

class PSCQuestionExtraction(BaseModel):
    questions: List[Question] = Field(
        ..., 
        description="Array of extracted questions from the PDF"
    )
    metadata: Optional[DocumentMetadata] = Field(
        None, 
        description="Metadata about the PDF document"
    )

    model_config = ConfigDict(use_enum_values=True)