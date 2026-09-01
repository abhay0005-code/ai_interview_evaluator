import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import DATABASE_PATH


def _now():
    return datetime.now(timezone.utc).isoformat()


def conn():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _add_column(connection, table, column, definition):
    existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    connection = conn()
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
        question TEXT NOT NULL UNIQUE, difficulty TEXT NOT NULL, priority INTEGER DEFAULT 0,
        active INTEGER DEFAULT 1, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_name TEXT, category TEXT,
        candidate_email TEXT, target_role TEXT, experience_years TEXT,
        provider TEXT, model TEXT, started_at TEXT NOT NULL,
        status TEXT DEFAULT 'in_progress', ended_at TEXT, final_score REAL,
        final_feedback TEXT
    );
    CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL, answer TEXT, response_time_seconds REAL, score REAL,
        correctness REAL, completeness REAL, depth REAL, clarity REAL, strengths TEXT,
        missing_points TEXT, suggestions TEXT, created_at TEXT NOT NULL,
        FOREIGN KEY(session_id) REFERENCES sessions(id), FOREIGN KEY(question_id) REFERENCES questions(id)
    );
    """)
    _add_column(connection, "sessions", "status", "TEXT DEFAULT 'in_progress'")
    _add_column(connection, "sessions", "ended_at", "TEXT")
    _add_column(connection, "sessions", "candidate_email", "TEXT")
    _add_column(connection, "sessions", "target_role", "TEXT")
    _add_column(connection, "sessions", "experience_years", "TEXT")
    _add_column(connection, "sessions", "final_score", "REAL")
    _add_column(connection, "sessions", "final_feedback", "TEXT")
    connection.commit()
    connection.close()


def seed_questions(items, force=False):
    connection = conn()
    if force:
        connection.execute("DELETE FROM questions")
    for item in items:
        connection.execute("""INSERT OR IGNORE INTO questions
            (category, question, difficulty, priority, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)""",
            (item["category"], item["question"], item["difficulty"], item["priority"], _now()))
    connection.commit()
    connection.close()


def add_question(category, question, difficulty="Medium", priority=0):
    question = (question or "").strip()
    category = (category or "").strip()
    if not category or not question:
        raise ValueError("Category and question are required.")
    connection = conn()
    connection.execute("""INSERT OR IGNORE INTO questions
        (category, question, difficulty, priority, active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)""", (category, question, difficulty, int(priority), _now()))
    connection.commit()
    connection.close()


def count_questions():
    connection = conn()
    count = connection.execute("SELECT COUNT(*) FROM questions WHERE active=1").fetchone()[0]
    connection.close()
    return count


def list_questions(category="All", difficulty=None):
    connection = conn()
    sql, params = "SELECT * FROM questions WHERE active=1", []
    if category and category != "All":
        sql += " AND category=?"; params.append(category)
    if difficulty and difficulty != "All":
        sql += " AND difficulty=?"; params.append(difficulty)
    rows = connection.execute(sql + " ORDER BY priority DESC, id", params).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_question(question_id):
    connection = conn(); row = connection.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone(); connection.close()
    return dict(row) if row else None


def create_session(name, category, provider, model, email="", target_role="", experience_years=""):
    connection = conn()
    cursor = connection.execute("""INSERT INTO sessions
        (candidate_name,candidate_email,target_role,experience_years,category,provider,model,started_at)
        VALUES(?,?,?,?,?,?,?,?)""", (name, email, target_role, experience_years, category, provider, model, _now()))
    connection.commit(); session_id = cursor.lastrowid; connection.close()
    return session_id


def save_attempt(session_id, question_id, answer, elapsed, evaluation):
    connection = conn()
    cursor = connection.execute("""INSERT INTO attempts
        (session_id,question_id,answer,response_time_seconds,score,correctness,completeness,depth,clarity,strengths,missing_points,suggestions,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (session_id, question_id, answer, elapsed, evaluation["score"], evaluation["correctness"], evaluation["completeness"], evaluation["depth"], evaluation["clarity"], evaluation.get("strengths", ""), evaluation.get("missing_points", ""), evaluation.get("suggestions", ""), _now()))
    connection.commit(); attempt_id = cursor.lastrowid; connection.close()
    return attempt_id


def get_session(session_id):
    connection = conn(); row = connection.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone(); connection.close()
    return dict(row) if row else None


def get_attempts(session_id):
    connection = conn()
    rows = connection.execute("""SELECT a.*, q.question, q.category FROM attempts a
        JOIN questions q ON q.id=a.question_id WHERE a.session_id=? ORDER BY a.id""", (session_id,)).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def end_session(session_id, final_score=None, final_feedback=None):
    connection = conn()
    connection.execute("""UPDATE sessions SET status='completed', ended_at=?,
        final_score=?, final_feedback=? WHERE id=?""", (_now(), final_score, final_feedback, session_id))
    connection.commit(); connection.close()


def list_candidate_reports():
    connection = conn()
    rows = connection.execute("""SELECT id, candidate_name, candidate_email, target_role,
        experience_years, category, final_score, final_feedback, started_at, ended_at, status
        FROM sessions WHERE status='completed' ORDER BY ended_at DESC, id DESC""").fetchall()
    connection.close()
    return [dict(row) for row in rows]
