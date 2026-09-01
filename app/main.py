import json
import secrets
import time
import gradio as gr

from .service import InterviewService
from .config import PROVIDERS, MODELS, VECTOR_PROVIDERS, OPEN_SOURCE_MODELS, ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_ACCESS_MODE
from .admin import load_settings, save_settings
from .reports import build_report, export_pdf, export_excel, export_csv, export_json
from .evaluator import review_final_outcome

svc = InterviewService()
settings = load_settings()

SECTIONS = settings["sections"]
PROVIDERS_UI = [
    "Ollama (Local)",
    "Hugging Face (Inference API)",
    "Hugging Face / Transformers (Local)",
    "OpenAI / ChatGPT",
    "Anthropic / Claude",
]

def model_choices(provider):
    if provider == "Hugging Face (Inference API)":
        return OPEN_SOURCE_MODELS["Hugging Face / Transformers (Local)"]
    if provider in OPEN_SOURCE_MODELS:
        return OPEN_SOURCE_MODELS[provider]
    # Support the existing provider configuration.
    try:
        return MODELS[PROVIDERS[provider]]
    except Exception:
        return []

def connect_vector(label):
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[label])
        return f"🟢 **{label} connected** · RAG records: **{svc.vector_count()}**"
    except Exception as e:
        return f"🔴 **{label} connection failed:** `{e}`"

def save_admin(section, difficulty, count, adaptive, time_limit, provider,
               model, vector_db, top_k, temperature):
    global settings
    settings = save_settings({
        "sections": [section] if section else [SECTIONS[0]],
        "difficulty": difficulty,
        "questions_per_session": int(count),
        "adaptive": bool(adaptive),
        "time_limit_seconds": int(time_limit),
        "provider": provider,
        "model": model,
        "vector_db": vector_db,
        "rag_top_k": int(top_k),
        "temperature": float(temperature),
    })
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        rag_count = svc.vector_count()
    except Exception:
        rag_count = "connection error"
    return f"✅ **Admin configuration saved.**  Section: `{section}` · LLM: `{provider} / {model}` · Vector DB: `{vector_db}` · RAG records: `{rag_count}`"

def apply_admin_section(section):
    return section if section else SECTIONS[0]

def refresh_admin():
    s = load_settings()
    return (
        (s["sections"][0] if isinstance(s["sections"], list) and s["sections"] else SECTIONS[0]), s["difficulty"], s["questions_per_session"],
        s["adaptive"], s["time_limit_seconds"], s["provider"], s["model"],
        s["vector_db"], s["rag_top_k"], s["temperature"]
    )

def start(name, email, target_role, experience_years, section, provider, model, vector_db):
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        # Map UI provider labels to service provider names where possible.
        provider_key = PROVIDERS.get(provider, provider)
        sid, q = svc.start(name or "Candidate", section, provider_key, model, settings["difficulty"],
                           email or "", target_role or "", experience_years or "")
        if not q:
            sid, q = svc.start(name or "Candidate", section, provider_key, model,
                               email=email or "", target_role=target_role or "", experience_years=experience_years or "")
        if not q or not isinstance(q, dict) or not q.get("question"):
            raise RuntimeError("No valid question was returned. Check the selected LLM/model and API configuration.")
        qtext = q["question"]
        return str(sid), qtext, f"### Question\n\n{qtext}", time.time(), "🟢 Interview started"
    except Exception as e:
        return "", "", f"🔴 {e}", time.time(), f"🔴 {e}"

def submit(sid, question, answer, t0, provider, model, section, vector_db):
    if not sid:
        return "Start an interview first.", question, f"### Question\n\n{question}", time.time(), "No active session"
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        provider_key = PROVIDERS.get(provider, provider)
        elapsed = max(0, time.time() - (t0 or time.time()))
        if not answer or not answer.strip():
            raise ValueError("Enter an answer before requesting an evaluation.")
        result = svc.answer(sid, question, answer, elapsed, provider_key, model, section,
                            settings["temperature"], settings["rag_top_k"],
                            settings["questions_per_session"], settings["adaptive"])
        if not result or not isinstance(result, (tuple, list)) or len(result) < 2:
            raise RuntimeError("LLM evaluation returned no usable result.")
        evaluation, nextq = result[0], result[1]
        ev = evaluation if isinstance(evaluation, dict) else {"feedback": str(evaluation) if evaluation else "No evaluation returned."}
        report = (
            "### 🧠 AI Evaluation\n"
            f"**Score:** {ev.get('score','-')}/10  \n"
            f"**Correctness:** {ev.get('correctness','-')}  \n"
            f"**Completeness:** {ev.get('completeness','-')}  \n"
            f"**Technical Depth:** {ev.get('technical_depth','-')}  \n"
            f"**Clarity:** {ev.get('clarity','-')}  \n"
            f"**Feedback:** {ev.get('feedback', ev.get('improvement',''))}"
        )
        next_text = nextq.get("question") if isinstance(nextq, dict) else None
        next_text = next_text or "🎉 No more questions."
        return report, next_text, f"### Question\n\n{next_text}", time.time(), f"⏱️ {elapsed:.1f}s · Saved to SQLite + RAG"
    except Exception as e:
        return f"🔴 Evaluation failed: `{e}`", question, f"### Question\n\n{question}", time.time(), f"🔴 {e}"

def skip_question(sid, question, section):
    try:
        questions = svc.questions(section)
        current = next((q for q in questions if q["question"] == question), None)
        attempts = svc.get_attempts(sid)
        used = {a.get("question_id") for a in attempts}
        remaining = [q for q in questions if q.get("id") not in used and (not current or q.get("id") != current.get("id"))]
        q = remaining[0] if remaining else None
        text = q["question"] if q else "🎉 No more questions."
        return text, f"### Question\n\n{text}", time.time(), "⏭️ Question skipped"
    except Exception as e:
        return question, f"### Question\n\n{question}", time.time(), f"🔴 {e}"

def end_interview(sid):
    if not sid:
        return "No active interview.", None, None
    try:
        session, attempts = svc.end_session(sid)
        report = build_report(session, attempts)
        svc.save_final_outcome(sid, report["overall_score"], report["overall_feedback"])
        md = render_report(report)
        return md, report, "🔴 Interview ended"
    except Exception as e:
        return f"🔴 {e}", None, f"🔴 {e}"

def render_report(report):
    if not report:
        return "No report."
    avg = report.get("overall_score", 0)
    grade = "🟢 Strong" if avg >= 8 else ("🟡 Needs Improvement" if avg >= 6 else "🔴 Needs Preparation")
    md = f"""# 📊 Interview Outcome

## {avg:.1f}/10 — {grade}

### Overall feedback

{report.get('overall_feedback', 'No overall feedback is available.')}

| Metric | Result |
|---|---|
| Candidate | {report.get('candidate','')} |
| Section | {report.get('section','')} |
| LLM | {report.get('llm_provider','')} / {report.get('llm_model','')} |
| Questions | {report.get('questions_attempted',0)} |
| Status | {report.get('status','')} |

"""
    for i, a in enumerate(report.get("attempts", []), 1):
        ev = a.get("evaluation") or {}
        md += f"""### {i}. {a.get('question','')}

**Answer:** {a.get('answer','')}

**Score:** {ev.get('score', a.get('score','-'))}/10

**Feedback:** {ev.get('feedback', ev.get('improvement',''))}

---
"""
    return md

def refresh_candidate_reports():
    reports = svc.candidate_reports()
    return [[
        report["id"], report.get("candidate_name", ""), report.get("candidate_email", ""),
        report.get("target_role", ""), report.get("experience_years", ""), report.get("category", ""),
        report.get("final_score", ""), report.get("final_feedback", ""), report.get("ended_at", "")
    ] for report in reports]

def refresh_questions():
    return [[item["id"], item["category"], item["question"], item["difficulty"], item["priority"]]
            for item in svc.questions("All")]

def add_question_ui(category, question, difficulty, priority):
    try:
        svc.add_question(category, question, difficulty, priority)
        return f"Added question. Active questions: {svc.question_count()}", refresh_questions()
    except Exception as error:
        return f"Unable to add question: {error}", refresh_questions()

def _rag_rows(records):
    return [[record.get("text", ""), json.dumps(record.get("metadata", {}), ensure_ascii=False), record.get("distance", "")]
            for record in records]

def refresh_rag_memory(vector_db):
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        return f"Connected to {vector_db}. Stored records: {svc.vector_count()}", _rag_rows(svc.rag_preview(100))
    except Exception as error:
        return f"Unable to read RAG memory: {error}", []

def add_rag_memory(vector_db, question, answer, feedback, score):
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        svc.add_rag_memory(question, answer, feedback, score)
        return f"RAG memory saved. Stored records: {svc.vector_count()}", _rag_rows(svc.rag_preview(100))
    except Exception as error:
        return f"Unable to save RAG memory: {error}", []

def search_rag_memory(vector_db, query, top_k):
    try:
        svc.set_vector_store(VECTOR_PROVIDERS[vector_db])
        return _rag_rows(svc.search_rag(query, top_k))
    except Exception:
        return []

def compare_final_result(report, provider, model):
    if not report:
        return "Complete an interview first to compare its final result."
    try:
        result = review_final_outcome(provider, model, report, settings["temperature"])
        original = float(report.get("overall_score", 0))
        compared = float(result["overall_score"])
        difference = compared - original
        direction = "+" if difference >= 0 else ""
        return f"""## Second-model final review

| Metric | Result |
|---|---|
| Original score | {original:.1f}/10 |
| {provider} / {model} | {compared:.1f}/10 |
| Difference | {direction}{difference:.1f} |

**Overall feedback:** {result['overall_feedback']}

**Strengths:** {result['strengths']}

**Improvement areas:** {result['improvement_areas']}"""
    except Exception as error:
        return f"Comparison failed: `{error}`"

def apply_user_mode(role):
    is_admin_request = role == "Admin"
    if is_admin_request and ADMIN_ACCESS_MODE == "open":
        return (
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
            gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
            gr.update(visible=False), "**Open admin mode enabled for all visitors.**",
        )
    message = ("Enter administrator credentials to unlock protected tabs."
               if is_admin_request else
               "**Candidate mode enabled.** Use the Interview tab to start and complete your interview.")
    return (
        gr.update(visible=False), gr.update(visible=True), gr.update(visible=True),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=is_admin_request), message,
    )

def unlock_admin(username, password):
    username = (username or "").strip()
    if not ADMIN_PASSWORD:
        message = "Admin access is disabled. Set `ADMIN_PASSWORD` in `.env`, then restart the app."
        return (gr.update(visible=False),) * 4 + (message,)
    valid = secrets.compare_digest(username, ADMIN_USERNAME) and secrets.compare_digest(password or "", ADMIN_PASSWORD)
    if not valid:
        return (gr.update(visible=False),) * 4 + ("Invalid administrator credentials.",)
    return (
        gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True),
        "**Admin access enabled for this browser session.**",
    )

with gr.Blocks(title="AI Interview Evaluator", theme=gr.themes.Soft()) as demo:
    with gr.Row():
        user_mode = gr.Radio(["Candidate", "Admin"], value="Candidate", label="Use app as")
        user_mode_status = gr.Markdown("**Candidate mode enabled.** Use the Interview tab to start and complete your interview.")
    with gr.Row(visible=False) as admin_login:
        admin_username = gr.Textbox(label="Administrator username", value=ADMIN_USERNAME)
        admin_password = gr.Textbox(label="Administrator password", type="password")
        unlock_admin_btn = gr.Button("Unlock Admin", variant="primary")
    gr.Markdown("# 🎯 AI Interview Evaluator\n### Adaptive AI interview platform with LLM judging + RAG memory")

    with gr.Tab("🔐 Admin", visible=False) as admin_tab:
        gr.Markdown("## Interview Administration")
        gr.Markdown("Configure the interview before starting a candidate session. Select exactly one interview section.")
        with gr.Row():
            with gr.Column():
                admin_sections = gr.Dropdown(SECTIONS, value=(settings["sections"][0] if isinstance(settings["sections"], list) and settings["sections"] else SECTIONS[0]), multiselect=False, label="Interview Section")
                difficulty = gr.Dropdown(["Junior", "Mid-Level", "Senior", "Expert"], value=settings["difficulty"], label="Difficulty")
                question_count = gr.Slider(1, 50, value=settings["questions_per_session"], step=1, label="Questions per Session")
                adaptive = gr.Checkbox(value=settings["adaptive"], label="Adaptive questioning using RAG")
                time_limit = gr.Slider(30, 600, value=settings["time_limit_seconds"], step=30, label="Time limit per question (seconds)")
            with gr.Column():
                admin_provider = gr.Dropdown(PROVIDERS_UI, value=settings["provider"], label="LLM Provider")
                admin_model = gr.Dropdown(model_choices(settings["provider"]), value=settings["model"], label="LLM Model")
                admin_vector = gr.Dropdown(["ChromaDB (Local)", "FAISS (Local)", "Qdrant", "Pinecone"], value=settings["vector_db"], label="Default Vector DB")
                rag_top_k = gr.Slider(1, 20, value=settings["rag_top_k"], step=1, label="RAG Top-K")
                temperature = gr.Slider(0, 1, value=settings["temperature"], step=0.05, label="LLM Temperature")
        with gr.Row():
            save_admin_btn = gr.Button("💾 Save Admin Configuration", variant="primary")
            refresh_admin_btn = gr.Button("🔄 Reload Settings")
            apply_section_btn = gr.Button("➡️ Apply Section to Interview")
        admin_status = gr.Markdown()
        hf_help = gr.Markdown("**Hugging Face:** set `HUGGINGFACEHUB_API_TOKEN` (or `HF_TOKEN`) in `.env` when using Hugging Face Inference API.")

    with gr.Tab("🎤 Interview") as interview_tab:
        with gr.Row():
            with gr.Column(scale=1):
                candidate = gr.Textbox(label="Candidate Name", value="Candidate")
                candidate_email = gr.Textbox(label="Candidate Email")
                target_role = gr.Textbox(label="Target Role")
                experience_years = gr.Textbox(label="Experience (years)")
                interview_section = gr.Dropdown(SECTIONS, value=settings["sections"][0], label="Interview Section")
                provider = gr.Dropdown(PROVIDERS_UI, value=settings["provider"], label="LLM Provider")
                model = gr.Dropdown(model_choices(settings["provider"]), value=settings["model"], label="LLM Model")
                vector_db = gr.Dropdown(["ChromaDB (Local)", "FAISS (Local)", "Qdrant", "Pinecone"], value=settings["vector_db"], label="🧠 Vector DB")
                vector_status = gr.Markdown("🟢 ChromaDB (Local) is the default")
                connect_btn = gr.Button("🔌 Connect Vector DB")
                start_btn = gr.Button("🚀 Start Interview", variant="primary")
                end_btn = gr.Button("⛔ End Interview", variant="stop")
            with gr.Column(scale=2):
                session = gr.Textbox(label="Session ID", interactive=False)
                question_md = gr.Markdown("### Question\n\nStart the interview.")
                current_question = gr.Textbox(visible=False)
                answer = gr.Textbox(label="Candidate Answer", lines=10)
                timer = gr.Number(value=0, visible=False)
                with gr.Row():
                    submit_btn = gr.Button("✅ Submit & Evaluate", variant="primary")
                    skip_btn = gr.Button("⏭️ Skip")
                evaluation = gr.Markdown()
                status = gr.Markdown()

    with gr.Tab("📊 Results") as results_tab:
        final_report = gr.Markdown("End an interview to generate the dashboard.")
        report_state = gr.State(None)
        with gr.Row():
            pdf_btn = gr.Button("📄 Generate PDF")
            excel_btn = gr.Button("📊 Generate Excel")
            csv_btn = gr.Button("🧾 Generate CSV")
            json_btn = gr.Button("🔧 Generate JSON")
        with gr.Row():
            pdf_file = gr.File(label="PDF Report")
            excel_file = gr.File(label="Excel Report")
            csv_file = gr.File(label="CSV Report")
            json_file = gr.File(label="JSON Report")
        gr.Markdown("## Compare final result with another LLM")
        with gr.Row():
            comparison_provider = gr.Dropdown(PROVIDERS_UI, value=settings["provider"], label="Comparison LLM Provider")
            comparison_model = gr.Dropdown(model_choices(settings["provider"]), value=settings["model"], label="Comparison Model")
            compare_result_btn = gr.Button("Compare Final Result", variant="secondary")
        comparison_result = gr.Markdown()

    with gr.Tab("Candidate Reports", visible=False) as candidate_reports_tab:
        gr.Markdown("## Completed candidate interviews")
        refresh_reports_btn = gr.Button("Refresh Candidate Reports")
        candidate_reports_table = gr.Dataframe(
            headers=["Session ID", "Candidate", "Email", "Target Role", "Experience", "Section", "Final Score", "Overall Feedback", "Completed At"],
            datatype=["number", "str", "str", "str", "str", "str", "number", "str", "str"],
            interactive=False,
            label="Candidate Reports",
        )

    with gr.Tab("Question Database", visible=False) as question_database_tab:
        gr.Markdown("## Read and write interview questions")
        refresh_questions_btn = gr.Button("Refresh Questions")
        questions_table = gr.Dataframe(
            headers=["ID", "Category", "Question", "Difficulty", "Priority"],
            datatype=["number", "str", "str", "str", "number"], interactive=False,
            label="Stored Questions",
        )
        with gr.Row():
            db_category = gr.Textbox(label="Category")
            db_difficulty = gr.Dropdown(["Junior", "Mid-Level", "Senior", "Expert", "Medium", "Hard"], value="Medium", label="Difficulty")
            db_priority = gr.Number(value=0, precision=0, label="Priority")
        db_question = gr.Textbox(label="New Question", lines=3)
        add_question_btn = gr.Button("Add Question", variant="primary")
        db_status = gr.Markdown()

    with gr.Tab("RAG Memory", visible=False) as rag_memory_tab:
        gr.Markdown("## Read, write, and retrieve vector-memory records")
        rag_vector_db = gr.Dropdown(["ChromaDB (Local)", "FAISS (Local)", "Qdrant", "Pinecone"], value=settings["vector_db"], label="Vector DB")
        refresh_rag_btn = gr.Button("Refresh Stored RAG Memory")
        rag_status = gr.Markdown()
        rag_memory_table = gr.Dataframe(
            headers=["Memory Text", "Metadata", "Distance"], datatype=["str", "str", "number"],
            interactive=False, label="Stored / Retrieved RAG Memory",
        )
        with gr.Row():
            rag_question = gr.Textbox(label="Memory Question")
            rag_score = gr.Number(value=0, minimum=0, maximum=10, label="Score")
        rag_answer = gr.Textbox(label="Memory Answer", lines=3)
        rag_feedback = gr.Textbox(label="Memory Feedback / Notes", lines=2)
        add_rag_btn = gr.Button("Save RAG Memory", variant="primary")
        with gr.Row():
            rag_query = gr.Textbox(label="Search Query")
            rag_top_k = gr.Slider(1, 20, value=5, step=1, label="Top K")
            search_rag_btn = gr.Button("Retrieve Similar Memory")

    # Admin interactions
    user_mode.change(
        apply_user_mode,
        inputs=user_mode,
        outputs=[admin_tab, interview_tab, results_tab, candidate_reports_tab, question_database_tab, rag_memory_tab, admin_login, user_mode_status],
    )
    unlock_admin_btn.click(
        unlock_admin,
        inputs=[admin_username, admin_password],
        outputs=[admin_tab, candidate_reports_tab, question_database_tab, rag_memory_tab, user_mode_status],
    )
    admin_provider.change(
        lambda p: gr.update(choices=model_choices(p), value=model_choices(p)[0] if model_choices(p) else None),
        inputs=admin_provider, outputs=admin_model
    )
    save_admin_btn.click(
        save_admin,
        inputs=[admin_sections, difficulty, question_count, adaptive, time_limit, admin_provider, admin_model, admin_vector, rag_top_k, temperature],
        outputs=admin_status
    )
    refresh_admin_btn.click(
        refresh_admin,
        outputs=[admin_sections, difficulty, question_count, adaptive, time_limit, admin_provider, admin_model, admin_vector, rag_top_k, temperature]
    )
    apply_section_btn.click(
        apply_admin_section,
        inputs=admin_sections,
        outputs=interview_section
    )

    # Interview interactions
    provider.change(
        lambda p: gr.update(choices=model_choices(p), value=model_choices(p)[0] if model_choices(p) else None),
        inputs=provider, outputs=model
    )
    comparison_provider.change(
        lambda p: gr.update(choices=model_choices(p), value=model_choices(p)[0] if model_choices(p) else None),
        inputs=comparison_provider, outputs=comparison_model
    )
    connect_btn.click(connect_vector, inputs=vector_db, outputs=vector_status)
    start_btn.click(
        start,
        inputs=[candidate, candidate_email, target_role, experience_years, interview_section, provider, model, vector_db],
        outputs=[session, current_question, question_md, timer, status]
    )
    submit_btn.click(
        submit,
        inputs=[session, current_question, answer, timer, provider, model, interview_section, vector_db],
        outputs=[evaluation, current_question, question_md, timer, status]
    ).then(lambda: "", outputs=answer)
    skip_btn.click(
        skip_question,
        inputs=[session, current_question, interview_section],
        outputs=[current_question, question_md, timer, status]
    ).then(lambda: "", outputs=answer)
    end_btn.click(
        end_interview,
        inputs=session,
        outputs=[final_report, report_state, status]
    ).then(refresh_candidate_reports, outputs=candidate_reports_table)

    pdf_btn.click(lambda r: export_pdf(r) if r else None, inputs=report_state, outputs=pdf_file)
    excel_btn.click(lambda r: export_excel(r) if r else None, inputs=report_state, outputs=excel_file)
    csv_btn.click(lambda r: export_csv(r) if r else None, inputs=report_state, outputs=csv_file)
    json_btn.click(lambda r: export_json(r) if r else None, inputs=report_state, outputs=json_file)
    compare_result_btn.click(compare_final_result, inputs=[report_state, comparison_provider, comparison_model], outputs=comparison_result)
    refresh_reports_btn.click(refresh_candidate_reports, outputs=candidate_reports_table)
    refresh_questions_btn.click(refresh_questions, outputs=questions_table)
    add_question_btn.click(add_question_ui, inputs=[db_category, db_question, db_difficulty, db_priority], outputs=[db_status, questions_table])
    refresh_rag_btn.click(refresh_rag_memory, inputs=rag_vector_db, outputs=[rag_status, rag_memory_table])
    add_rag_btn.click(add_rag_memory, inputs=[rag_vector_db, rag_question, rag_answer, rag_feedback, rag_score], outputs=[rag_status, rag_memory_table])
    search_rag_btn.click(search_rag_memory, inputs=[rag_vector_db, rag_query, rag_top_k], outputs=rag_memory_table)

if __name__ == "__main__":
    demo.launch()
