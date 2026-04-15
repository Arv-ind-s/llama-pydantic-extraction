import pytest
from src.extractors.question_extractor import link_diagram_paths

def test_link_diagram_paths_exact_match():
    questions = [
        {"question_number": 1, "has_question_diagram": True, "question_diagram_path": None},
        {"question_number": 11, "has_question_diagram": True, "question_diagram_path": None}
    ]
    image_paths = ["/tmp/q1.png", "/tmp/q11.png"]
    
    linked = link_diagram_paths(questions, image_paths, "test.pdf")
    
    assert linked[0]["question_diagram_path"] == "/tmp/q1.png"
    assert linked[1]["question_diagram_path"] == "/tmp/q11.png"

def test_link_diagram_paths_no_diagram():
    questions = [{"question_number": 1, "has_question_diagram": False, "question_diagram_path": None}]
    image_paths = ["/tmp/q1.png"]
    
    linked = link_diagram_paths(questions, image_paths, "test.pdf")
    assert linked[0]["question_diagram_path"] is None

def test_link_diagram_paths_complex_names():
    questions = [{"question_number": 5, "has_question_diagram": True, "question_diagram_path": None}]
    image_paths = ["/tmp/page_12_image_5.jpg", "/tmp/image_55.png"]
    
    linked = link_diagram_paths(questions, image_paths, "test.pdf")
    assert linked[0]["question_diagram_path"] == "/tmp/page_12_image_5.jpg"

def test_link_answer_diagrams():
    questions = [{
        "question_number": 1,
        "answer_options": {"A": "Opt A", "B": "Opt B"},
        "has_answer_diagrams": True,
        "answer_diagram_paths": {}
    }]
    image_paths = ["/tmp/q1_ans_A.png", "/tmp/q2_ans_A.png"]
    
    linked = link_diagram_paths(questions, image_paths, "test.pdf")
    assert linked[0]["answer_diagram_paths"]["A"] == "/tmp/q1_ans_A.png"
    assert "B" not in linked[0]["answer_diagram_paths"]
