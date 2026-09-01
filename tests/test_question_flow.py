def test_question_flow_contract():
    text = open("app/main.py", encoding="utf-8").read()
    assert "outputs=[evaluation, current_question, question_md, timer, status]" in text
    assert "svc.answer(" in text
    assert "Enter an answer before requesting an evaluation." in text
