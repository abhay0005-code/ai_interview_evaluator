from app.reports import build_report


def test_report_includes_overall_candidate_feedback():
    report = build_report(
        {"candidate_name": "Ada", "category": "RAG"},
        [{"score": 7, "suggestions": "Explain retrieval evaluation metrics."}],
    )
    assert "overall_feedback" in report
    assert "7.0/10" in report["overall_feedback"]
    assert "retrieval evaluation metrics" in report["overall_feedback"]
