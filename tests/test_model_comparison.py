from app import evaluator


def test_second_model_review_parses_score(monkeypatch):
    class FakeClient:
        def __init__(self, *args):
            pass

        def generate(self, prompt):
            return '{"overall_score": 8, "overall_feedback": "Good", "strengths": "RAG", "improvement_areas": "Testing"}'

    monkeypatch.setattr(evaluator, "LLMClient", FakeClient)
    result = evaluator.review_final_outcome("ollama", "test", {
        "candidate": "Ada", "section": "RAG", "overall_score": 7,
        "attempts": [{"question": "What is RAG?", "answer": "Grounded generation.", "score": 7}],
    })
    assert result["overall_score"] == 8
    assert result["strengths"] == "RAG"
