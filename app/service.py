from . import db
from .evaluator import evaluate
from .questions import QUESTIONS
from .rag import InterviewRAG
import time


class InterviewService:
    def __init__(self):
        db.init_db()
        db.seed_questions(QUESTIONS)
        self.rag = InterviewRAG()

    def set_vector_store(self, provider):
        self.rag.switch(provider)

    def vector_count(self):
        return self.rag.count()

    def rag_preview(self, limit=20):
        return self.rag.preview(limit)

    def questions(self, category, difficulty=None):
        return db.list_questions(category, difficulty)

    def add_question(self, category, question, difficulty, priority):
        db.add_question(category, question, difficulty, priority)

    def question_count(self):
        return db.count_questions()

    def start(self, name, category, provider, model, difficulty=None, email="", target_role="", experience_years=""):
        questions = self.questions(category, difficulty)
        if not questions:
            return None, None
        return db.create_session(name, category, provider, model, email, target_role, experience_years), questions[0]

    def answer(self, session_id, question_text, answer, elapsed, provider, model, category,
               temperature=0.2, top_k=5, max_questions=None, adaptive=True):
        question = next((item for item in self.questions(category) if item["question"] == question_text), None)
        if not question:
            raise ValueError("The current question could not be found.")
        memory = self.rag.retrieve(question["question"], top_k, session_id=str(session_id))
        evaluation = evaluate(provider, model, question["question"], answer, elapsed, memory, temperature)
        attempt_id = db.save_attempt(session_id, question["id"], answer, elapsed, evaluation)
        self.rag.add(attempt_id, question["question"], answer, evaluation, session_id=session_id)
        used = {attempt["question_id"] for attempt in db.get_attempts(session_id)}
        if max_questions and len(used) >= max_questions:
            return evaluation, None
        remaining = [item for item in self.questions(category) if item["id"] not in used]
        next_question = None if not remaining else (remaining[0] if not adaptive or evaluation["score"] < 6 else max(remaining, key=lambda item: item["priority"]))
        return evaluation, next_question

    def get_session(self, session_id):
        return db.get_session(session_id)

    def get_attempts(self, session_id):
        return db.get_attempts(session_id)

    def end_session(self, session_id):
        db.end_session(session_id)
        return db.get_session(session_id), db.get_attempts(session_id)

    def save_final_outcome(self, session_id, score, feedback):
        db.end_session(session_id, score, feedback)

    def candidate_reports(self):
        return db.list_candidate_reports()

    def add_rag_memory(self, question, answer, feedback, score=0):
        if not (question or "").strip() or not (answer or "").strip():
            raise ValueError("Question and answer are required to create RAG memory.")
        record_id = int(time.time() * 1000)
        self.rag.add(record_id, question.strip(), answer.strip(), {
            "score": float(score), "feedback": feedback or "Manual RAG memory",
            "suggestions": feedback or "Manual RAG memory",
        }, session_id="manual")
        return record_id

    def search_rag(self, query, top_k=5):
        if not (query or "").strip():
            return []
        return self.rag.retrieve(query.strip(), int(top_k))
