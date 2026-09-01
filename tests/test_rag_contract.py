def test_rag_contract():
    rag = open("app/rag.py", encoding="utf-8").read()
    main = open("app/main.py", encoding="utf-8").read()
    service = open("app/service.py", encoding="utf-8").read()
    for name in ["ChromaStore", "FaissStore", "QdrantStore", "PineconeStore"]:
        assert f"class {name}" in rag
    assert "self.rag.add" in service and "session_id=session_id" in service
    assert "Vector DB" in main
    assert "rag_top_k" in main
