from .reports import build_report, export_pdf, export_excel, export_csv, export_json

def render_dashboard(session, attempts):
    report = build_report(session, attempts)
    scores = []
    areas = {}
    for a in attempts:
        ev = a.get("evaluation") or {}
        score = ev.get("score", a.get("score"))
        try:
            score = float(score)
        except Exception:
            continue
        scores.append(score)
        category = a.get("category") or session.get("category") or "Interview"
        areas.setdefault(category, []).append(score)

    avg = report["overall_score"]
    strongest = max(areas.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if areas else "-"
    weakest = min(areas.items(), key=lambda x: sum(x[1])/len(x[1]))[0] if areas else "-"

    area_lines = []
    for k, vals in sorted(areas.items()):
        area_lines.append(f"| {k} | {sum(vals)/len(vals):.1f}/10 |")
    area_table = "\n".join(area_lines) or "| - | - |"

    md = f"""
# 📊 Interview Outcome

### {avg:.1f} / 10

### Overall feedback

{report.get('overall_feedback', 'No overall feedback is available.')}

| Metric | Result |
|---|---:|
| Candidate | {session.get("candidate","")} |
| Section | {session.get("category","")} |
| Questions attempted | {len(attempts)} |
| Strongest area | {strongest} |
| Focus area | {weakest} |

### Section performance

| Section | Score |
|---|---:|
{area_table}

### Question-by-question review

"""
    for i, a in enumerate(attempts, 1):
        ev = a.get("evaluation") or {}
        md += (
            f"**{i}. {a.get('question','')}**  \n"
            f"**Answer:** {a.get('answer','')}  \n"
            f"**Score:** {ev.get('score', a.get('score','-'))}/10  \n"
            f"**Feedback:** {ev.get('feedback', ev.get('improvement',''))}  \n\n"
        )
    return md, report
