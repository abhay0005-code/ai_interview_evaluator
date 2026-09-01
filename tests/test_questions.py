from app.questions import QUESTIONS
def test_question_bank():
    assert len(QUESTIONS) >= 80
    assert any(x["category"] == "RAG" for x in QUESTIONS)
