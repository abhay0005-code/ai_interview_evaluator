import json,re
from .llm_provider import LLMClient

SYSTEM = """
You are a senior AI technical interviewer.
Evaluate the candidate's answer strictly against the interview question.

Return ONLY JSON:
{
 "score": 0-10,
 "correctness": 0-10,
 "completeness": 0-10,
 "depth": 0-10,
 "clarity": 0-10,
 "strengths": "string",
 "missing_points": "string",
 "suggestions": "string",
 "next_question_direction": "string"
}

Do not reward confident incorrect statements.
For system architecture questions consider scalability, security, reliability,
observability, maintainability and cost where applicable.
For coding questions consider correctness, complexity, edge cases and production quality.
"""

FINAL_REVIEW_SYSTEM = """
You are an independent senior technical-interview reviewer. Review the completed
interview evidence and return ONLY JSON in this format:
{
 "overall_score": 0-10,
 "overall_feedback": "string",
 "strengths": "string",
 "improvement_areas": "string"
}
Do not simply repeat the original evaluator score. Base the result on candidate
answers and give concise, evidence-based feedback.
"""

def evaluate(provider_name,model,question,answer,elapsed,memory,temperature=0.2):
    context="\n\n".join(item["text"] if isinstance(item,dict) else str(item) for item in memory) if memory else "No previous attempts."
    prompt=f"""
Question:
{question}

Candidate answer:
{answer}

Response time:
{elapsed:.1f} seconds

Retrieved RAG memory (retrieved before this request is sent to the LLM):
{context}

Use retrieved memory only to personalize feedback and identify recurring gaps.
Evaluate the current answer now.
"""
    raw=LLMClient(provider_name, model, temperature).generate(f"{SYSTEM}\n\n{prompt}")
    try:
        result=json.loads(raw)
    except Exception:
        m=re.search(r"\{.*\}",raw,re.S)
        if not m: raise ValueError("LLM did not return valid JSON.")
        result=json.loads(m.group())
    for key in ["score","correctness","completeness","depth","clarity"]:
        result[key]=max(0,min(10,float(result.get(key,0))))
    result.setdefault("strengths", "")
    result.setdefault("missing_points", "")
    result.setdefault("suggestions", "")
    result["feedback"] = result.get("feedback") or result["suggestions"]
    result["technical_depth"] = result["depth"]
    return result


def review_final_outcome(provider_name, model, report, temperature=0.2):
    attempts = report.get("attempts", [])
    if not attempts:
        raise ValueError("A completed interview with at least one answer is required.")
    evidence = []
    for index, attempt in enumerate(attempts, 1):
        evidence.append(
            f"Question {index}: {attempt.get('question', '')}\n"
            f"Candidate answer: {attempt.get('answer', '')}\n"
            f"Original score: {attempt.get('score', '')}/10"
        )
    prompt = (
        f"Candidate: {report.get('candidate', '')}\n"
        f"Interview section: {report.get('section', '')}\n"
        f"Original overall score: {report.get('overall_score', '')}/10\n\n"
        "Interview evidence:\n" + "\n\n".join(evidence)
    )
    raw = LLMClient(provider_name, model, temperature).generate(f"{FINAL_REVIEW_SYSTEM}\n\n{prompt}")
    try:
        result = json.loads(raw)
    except Exception:
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            raise ValueError("The comparison model did not return valid JSON.")
        result = json.loads(match.group())
    result["overall_score"] = max(0, min(10, float(result.get("overall_score", 0))))
    for key in ("overall_feedback", "strengths", "improvement_areas"):
        result[key] = str(result.get(key, ""))
    return result
