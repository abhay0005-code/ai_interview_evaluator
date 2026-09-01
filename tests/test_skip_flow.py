def test_skip_flow_present():
    text = open("app/main.py", encoding="utf-8").read()
    assert "def skip_question(" in text
    assert "skip_btn = gr.Button" in text
    assert "skip_btn.click(" in text
    assert "outputs=[current_question, question_md, timer, status]" in text
