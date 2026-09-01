from app import db


def test_candidate_details_and_final_outcome_are_persisted():
    db.init_db()
    session_id = db.create_session("Ada", "RAG", "ollama", "test", "ada@example.com", "AI Engineer", "4")
    db.end_session(session_id, 8.5, "Strong retrieval knowledge.")
    report = next(item for item in db.list_candidate_reports() if item["id"] == session_id)
    assert report["candidate_email"] == "ada@example.com"
    assert report["target_role"] == "AI Engineer"
    assert report["final_score"] == 8.5
