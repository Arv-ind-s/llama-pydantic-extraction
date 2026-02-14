# 🦙 Llama-Pydantic-Extraction

A robust Python framework for extracting structured data from PDF documents using LlamaParse and Pydantic validation. Specifically designed for PSC (Public Service Commission) question-answer extraction but extensible to any PDF data extraction use case.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Models](#data-models)
- [Output Format](#output-format)
- [Advanced Usage](#advanced-usage)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

**Llama-Pydantic-Extraction** combines the power of LlamaParse's AI-driven PDF parsing with Pydantic's strict data validation to create a reliable, type-safe pipeline for extracting structured information from unstructured PDF documents.

### Use Cases

- 📚 Educational content extraction (exam questions, study materials)
- 📄 Form data extraction (applications, surveys)
- 📊 Report parsing (financial, medical, legal documents)
- 🗂️ Document digitization and archival
- 🔍 Content analysis and categorization

## ✨ Features

### Core Capabilities

- **🤖 AI-Powered Extraction**: Leverages LlamaParse for intelligent PDF content extraction
- **✅ Type-Safe Validation**: Pydantic models ensure data integrity and consistency
- **🖼️ Diagram Support**: Extracts and saves diagrams from questions and answers
- **🌐 Multi-Language**: Supports 13+ Indian and international languages
- **📦 Batch Processing**: Process multiple PDFs efficiently
- **🔄 Error Handling**: Robust error handling with detailed logging
- **📊 Metadata Tracking**: Captures extraction metadata for audit trails
- **🏷️ Smart Tagging**: Automatic categorization and tagging system

### Technical Features

- **Modular Architecture**: Clean separation of concerns
- **Extensible Design**: Easy to adapt for new document types
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Configuration Management**: YAML and environment-based configuration
- **CLI Interface**: Simple command-line tools for common tasks

## 🏗️ Architecture
```
┌─────────────────┐
│   PDF Files     │
│   (corpus/)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LlamaParse     │◄─── API Key Authentication
│  Extractor      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Data      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pydantic       │◄─── Schema Validation
│  Models         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Validated      │
│  JSON Output    │
│  (output/)      │
└─────────────────┘
```

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- LlamaParse API key ([Get it here](https://cloud.llamaindex.ai/))

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/llama-pydantic-extraction.git
cd llama-pydantic-extraction
```

### Step 2: Create Virtual Environment
```bash
# Using venv
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install in Development Mode (Optional)
```bash
pip install -e .
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
# Required: LlamaParse API Configuration
LLAMA_CLOUD_API_KEY=llx-your-api-key-here

# Optional: Processing Configuration
BATCH_SIZE=5
MAX_RETRIES=3
TIMEOUT=300
```

### YAML Configuration

Edit `config.yaml` for additional settings:
```yaml
# Extraction settings
extraction:
  languages:
    - English
    - Malayalam
    - Hindi
  
  categories:
    - History
    - Current Affairs
    - Geography
    - Science
    - Polity

# Output settings
output:
  save_diagrams: true
  diagram_format: png
  json_indent: 2
  
# Logging
logging:
  level: INFO
  save_logs: true
```

## 🚀 Usage

### Basic Usage

#### 1. Add PDF Files to Corpus
```bash
# Place your PDF files in the corpus directory
cp your_questions.pdf corpus/
```

#### 2. Run Extraction
```bash
# Process all PDFs in corpus directory
python scripts/extract_questions.py
```

#### 3. View Results

Extracted data will be saved in:
- `output/json/` - JSON files with extracted data
- `output/diagrams/` - Extracted diagrams (if any)
- `output/logs/` - Processing logs

### Command Line Options

#### Process All PDFs
```bash
python scripts/extract_questions.py
```

#### Process a Specific PDF
```bash
python scripts/extract_questions.py --file corpus/psc_exam_2024.pdf
```

#### Process with Pattern Matching
```bash
# Process only Kerala PSC files
python scripts/extract_questions.py --pattern "kerala_psc_*.pdf"

# Process only files from 2024
python scripts/extract_questions.py --pattern "*2024*.pdf"
```

#### Custom Corpus Directory
```bash
python scripts/extract_questions.py --corpus-dir /path/to/pdfs
```

#### Batch Processing
```bash
# Process multiple PDFs with progress tracking
python scripts/batch_process.py --workers 4
```

### Python API Usage
```python
from pathlib import Path
from src.processors.pdf_processor import PDFProcessor

# Initialize processor
processor = PDFProcessor()

# Process single PDF
pdf_path = Path("corpus/exam_questions.pdf")
result = processor.process_single_pdf(pdf_path)

# Access extracted data
print(f"Total questions: {len(result.questions)}")
for question in result.questions:
    print(f"Q: {question.question_text}")
    print(f"Answer: {question.correct_answer}")
    print(f"Category: {question.category}")
    print("---")

# Process entire corpus
results = processor.process_corpus()
print(f"Processed {len(results)} files successfully")
```

## 📊 Data Models

### Question Model Structure
```python
class Question(BaseModel):
    # Core Fields
    question_text: str                    # Full question text
    answer_options: Dict[str, str]        # {"A": "Option 1", "B": "Option 2"}
    correct_answer: str                   # "A" or "B" etc.
    
    # Categorization
    language: Language                    # Enum: English, Hindi, etc.
    category: Category                    # Enum: History, Science, etc.
    tags: QuestionTags                    # Nested model with metadata
    
    # Diagram Handling
    has_question_diagram: bool
    question_diagram_path: Optional[str]
    has_answer_diagrams: bool
    answer_diagram_paths: Dict[str, str]
    
    # Temporal Data
    has_temporal_relevance: bool          # Does answer change over time?
    
    # Optional Fields
    question_id: Optional[str]
    explanation: Optional[str]
    source: Optional[str]
    marks: Optional[float]
    negative_marking: Optional[bool]
```

### Supported Enums

#### Languages
```python
English, Hindi, Malayalam, Tamil, Telugu, Bengali, Marathi, 
Gujarati, Kannada, Odia, Punjabi, Urdu, Assamese
```

#### Categories
```python
History, Current Affairs, Geography, Science, Polity, Economics,
General Knowledge, Mathematics, Reasoning, English, Indian Culture,
Environment, Technology, Sports, Arts & Literature, Kerala State Affairs,
Indian Constitution, International Relations
```

#### Difficulty Levels
```python
easy, medium, hard
```

## 📤 Output Format

### JSON Structure
```json
{
  "questions": [
    {
      "question_text": "Who was the first Prime Minister of India?",
      "answer_options": {
        "A": "Jawaharlal Nehru",
        "B": "Mahatma Gandhi",
        "C": "Sardar Patel",
        "D": "Rajendra Prasad"
      },
      "has_question_diagram": false,
      "question_diagram_path": null,
      "language": "English",
      "category": "History",
      "tags": {
        "difficulty": "easy",
        "topic": "Indian Independence",
        "subtopic": "Post-Independence Leaders",
        "year_relevance": "1947",
        "importance": "high",
        "keywords": ["independence", "prime minister", "leader"]
      },
      "correct_answer": "A",
      "has_temporal_relevance": false,
      "has_answer_diagrams": false,
      "answer_diagram_paths": {},
      "question_id": "hist_001",
      "explanation": "Jawaharlal Nehru served as the first Prime Minister of independent India from 1947 to 1964.",
      "marks": 1.0,
      "negative_marking": false
    }
  ],
  "metadata": {
    "pdf_filename": "psc_history_questions.pdf",
    "extraction_date": "2024-02-14T10:30:00",
    "total_questions": 50,
    "exam_name": "Kerala PSC LDC Exam",
    "exam_date": "2024-01-15",
    "exam_year": 2024,
    "processing_notes": [
      "Successfully extracted all questions",
      "3 questions contain diagrams"
    ]
  }
}
```

### Directory Structure After Processing
```
llama-pydantic-extraction/
├── corpus/
│   └── psc_questions.pdf
├── output/
│   ├── json/
│   │   └── psc_questions_20240214_103000.json
│   ├── diagrams/
│   │   ├── question_1_diagram.png
│   │   ├── answer_A_diagram.png
│   │   └── answer_B_diagram.png
│   └── logs/
│       └── extraction_20240214_103000.log
```

## 🔧 Advanced Usage

### Custom Schema Extension

Create custom models for different document types:
```python
from src.models.question_schema import Question
from pydantic import BaseModel, Field

class MedicalQuestion(Question):
    """Extended model for medical exam questions"""
    medical_specialty: str = Field(..., description="Medical specialty area")
    clinical_relevance: bool = Field(default=False)
    case_based: bool = Field(default=False)
```

### Custom Extractor
```python
from src.extractors.llama_extractor import LlamaExtractor

class CustomExtractor(LlamaExtractor):
    def preprocess_pdf(self, pdf_path):
        """Add custom preprocessing logic"""
        # Your custom logic here
        pass
    
    def postprocess_data(self, data):
        """Add custom postprocessing logic"""
        # Your custom logic here
        return data
```

### Validation Only

Validate existing JSON files:
```python
python scripts/validate_output.py --file output/json/extracted_data.json
```

### Export to Different Formats
```python
from src.processors.pdf_processor import PDFProcessor
import csv

processor = PDFProcessor()
result = processor.process_single_pdf("corpus/questions.pdf")

# Export to CSV
with open('questions.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Question', 'Answer', 'Category', 'Difficulty'])
    
    for q in result.questions:
        writer.writerow([
            q.question_text,
            q.correct_answer,
            q.category,
            q.tags.difficulty
        ])
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=src --cov-report=html
```

### Run Specific Tests
```bash
# Test models only
pytest tests/test_models.py

# Test extractors only
pytest tests/test_extractors.py

# Verbose output
pytest -v
```

### Example Test
```python
# tests/test_models.py
from src.models.question_schema import Question, QuestionTags

def test_question_creation():
    question_data = {
        "question_text": "Test question?",
        "answer_options": {"A": "Option 1", "B": "Option 2"},
        "has_question_diagram": False,
        "language": "English",
        "category": "Science",
        "tags": {
            "difficulty": "medium",
            "topic": "Physics"
        },
        "correct_answer": "A",
        "has_temporal_relevance": False,
        "has_answer_diagrams": False
    }
    
    question = Question(**question_data)
    assert question.question_text == "Test question?"
    assert question.correct_answer == "A"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Error
```
ValueError: LLAMA_CLOUD_API_KEY not found in environment variables
```

**Solution**: Ensure your `.env` file exists and contains a valid API key.
```bash
echo "LLAMA_CLOUD_API_KEY=your_key_here" > .env
```

#### 2. Import Errors
```
ModuleNotFoundError: No module named 'src'
```

**Solution**: Ensure you're running scripts from the project root or install in development mode.
```bash
pip install -e .
```

#### 3. PDF Parsing Fails
```
Error extracting from file.pdf: Invalid PDF structure
```

**Solution**: 
- Ensure PDF is not corrupted
- Check if PDF is password-protected
- Verify PDF contains extractable text (not just scanned images)

#### 4. Validation Errors
```
ValidationError: 1 validation error for Question
```

**Solution**: Check the error message for specific field issues. Ensure your PDF structure matches the expected schema.

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or modify `config.yaml`:
```yaml
logging:
  level: DEBUG
```

## 📈 Performance Tips

1. **Batch Processing**: Use `batch_process.py` for multiple PDFs
2. **API Rate Limits**: Respect LlamaParse API limits (check your plan)
3. **Large PDFs**: Consider splitting very large PDFs before processing
4. **Caching**: LlamaParse caches results - reprocessing is faster
5. **Parallel Processing**: Use `--workers` flag for concurrent processing

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Write descriptive commit messages

### Code Formatting
```bash
# Format code with black
black src/ scripts/ tests/

# Check with flake8
flake8 src/ scripts/ tests/

# Type checking with mypy
mypy src/
```

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Schema Documentation](docs/SCHEMA.md)
- [Usage Examples](docs/USAGE.md)

## 🗺️ Roadmap

- [ ] Support for more document types (invoices, forms, reports)
- [ ] OCR integration for scanned PDFs
- [ ] Web interface for easy uploads
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] REST API endpoints
- [ ] Docker containerization
- [ ] Real-time processing dashboard
- [ ] Multi-model support (GPT-4, Claude)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LlamaIndex](https://www.llamaindex.ai/) for the amazing LlamaParse API
- [Pydantic](https://pydantic-docs.helpmanual.io/) for robust data validation
- Contributors and the open-source community

## 📧 Contact

- Project Link: [https://github.com/yourusername/llama-pydantic-extraction](https://github.com/yourusername/llama-pydantic-extraction)
- Issue Tracker: [https://github.com/yourusername/llama-pydantic-extraction/issues](https://github.com/yourusername/llama-pydantic-extraction/issues)

## ⭐ Show Your Support

If this project helped you, please give it a ⭐️!

---

**Made with ❤️ for the education and open-source community**