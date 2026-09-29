"""JEV / TypeSafe AI Cloud API Client."""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dotenv import load_dotenv

# Load .env from current directory or parent
env_paths = [
    Path(__file__).resolve().parent / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    Path(".env"),
]

for p in env_paths:
    if p.is_file():
        load_dotenv(p)
        # Fallback: if .env contains raw key without variable name
        content = p.read_text().strip()
        if content.startswith("apikey_"):
            os.environ["TYPESAFE_API_KEY"] = content


def get_jev_api_key(preferred_key: Optional[str] = None) -> Optional[str]:
    """Retrieve JEV / TypeSafe API key from argument or environment."""
    return (
        preferred_key
        or os.environ.get("TYPESAFE_API_KEY")
        or os.environ.get("JEV_API_KEY")
    )


def decide_jev(
    state: Union[str, Dict[str, Any]],
    questions: Dict[str, Dict[str, Any]],
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Call JEV / TypeSafe Cloud API for high-level decision."""
    key = get_jev_api_key(api_key)
    if not key or key == "your_api_key_here":
        raise ValueError(
            "Missing JEV API Key! Add TYPESAFE_API_KEY=your_key to .env or pass api_key."
        )

    from typesafe_sdk import TypeSafeClient, Choice, Score, Noul

    # Convert generic questions into TypeSafe SDK Question models
    sdk_questions = {}
    for qid, q in questions.items():
        qtype = q.get("type")
        instructions = q.get("instructions", "")
        criteria = q.get("criteria")

        if qtype == "choice":
            crit_dict = criteria if isinstance(criteria, dict) else {c: None for c in criteria}
            sdk_questions[qid] = Choice(instructions=instructions, criteria=crit_dict)
        elif qtype == "score":
            sdk_questions[qid] = Score(instructions=instructions, criteria=criteria)
        elif qtype == "noul":
            sdk_questions[qid] = Noul(instructions=instructions)
        else:
            raise ValueError(f"Unsupported question type for JEV: {qtype}")

    state_payload = {"text": state} if isinstance(state, str) else state

    with TypeSafeClient(api_key=key) as client:
        resp = client.system_one(state=state_payload, questions=sdk_questions)

    answers = {}
    values = {}

    for qid, ans in resp.answers.items():
        if hasattr(ans, "choice"):
            val = ans.choice
            answers[qid] = {
                "type": "choice",
                "choice": val,
                "confidence": getattr(ans, "confidence", 1.0),
                "probabilities": getattr(ans, "probabilities", {}),
            }
        elif hasattr(ans, "score"):
            val = ans.score
            answers[qid] = {
                "type": "score",
                "score": val,
                "confidence": getattr(ans, "confidence", 1.0),
                "probabilities": getattr(ans, "probabilities", {}),
            }
        elif hasattr(ans, "noul"):
            val = bool(ans.noul >= 0.5)
            answers[qid] = {
                "type": "noul",
                "noul": ans.noul,
                "confidence": getattr(ans, "confidence", 1.0),
            }
        else:
            val = None

        values[qid] = val

    return {
        "source": "jev-cloud-api",
        "values": values,
        "answers": answers,
        "usage": {
            "input_tokens": getattr(resp.usage, "input_tokens", 0),
            "output_tokens": 0,
        },
    }
