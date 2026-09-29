"""Basic unit and integration tests for Laya CoreML Agent."""

from pathlib import Path
import pytest
import sys

# Ensure parent directory is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import (
    DecisionResult,
    choice_question,
    score_question,
    noul_question,
    find_model_path,
    decide,
)


def test_question_schema_helpers():
    """Unit test: Question helper formats match Laya specifications."""
    cq = choice_question("Pick one", {"a": "Option A", "b": "Option B"})
    assert cq["type"] == "choice"
    assert "criteria" in cq

    sq = score_question("Rate urgency", ["low", "high"])
    assert sq["type"] == "score"
    assert isinstance(sq["criteria"], list)

    nq = noul_question("Should escalate?")
    assert nq["type"] == "noul"
    assert "instructions" in nq


def test_decision_result_shape_unit():
    """Unit test: DecisionResult correctly parses mock Laya output."""
    mock_raw = {
        "model": "laya-rl-agent",
        "answers": {
            "dept": {
                "type": "choice",
                "choice": "billing",
                "confidence": 0.99,
                "probabilities": {"billing": 0.99, "technical": 0.01},
            },
            "urgency": {
                "type": "score",
                "score": 1.5,
                "legend": {"0": "low", "1": "high"},
                "probabilities": {"0": 0.5, "1": 0.5},
            },
            "escalate": {
                "type": "noul",
                "noul": 0.85,
                "confidence": 0.85,
            },
        },
        "usage": {"input_tokens": 42, "output_tokens": 0},
    }

    res = DecisionResult(mock_raw)

    # Check direct dictionary access
    assert res["dept"] == "billing"
    assert res["urgency"] == 1.5
    assert res["escalate"] is True  # noul >= 0.5 is True
    assert res["usage"]["output_tokens"] == 0
    assert "answers" in res
    assert "values" in res


def test_integration_prediction():
    """Integration test: Real prediction running on local model."""
    model_path = find_model_path()
    if not Path(model_path).is_dir():
        pytest.skip(f"Local model not found at {model_path}, skipping live test.")

    questions = {
        "department": choice_question(
            "Which department?",
            {"billing": "Billing", "technical": "Technical", "sales": "Sales"},
        ),
        "urgency": score_question("Urgency?", ["low", "medium", "high"]),
        "escalate": noul_question("Escalate?"),
    }

    state = "The production server is completely down and failing."
    res = decide(state, questions, model_path=model_path, local_files_only=True)

    assert res["department"] in ["billing", "technical", "sales"]
    assert isinstance(res["urgency"], (int, float))
    assert isinstance(res["escalate"], bool)
    assert res["usage"]["output_tokens"] == 0
    assert res["usage"]["input_tokens"] > 0


def test_hybrid_escalation_logic():
    """Unit test: Hybrid pipeline triggers escalation on critical state."""
    from hybrid import triage_hybrid
    
    # Non-critical invoice request
    res_easy = triage_hybrid("Please send me last month's invoice.")
    assert res_easy["department"] == "billing"
    assert res_easy["escalated"] is False

    # Critical crash request
    res_hard = triage_hybrid("CRITICAL: All servers are down and failing completely!")
    assert res_hard["department"] == "technical"
    assert res_hard["escalated"] is True


def test_rank_wide_pipeline():
    """Unit & Integration test: Rank wide sorts tickets by priority and escalation."""
    from rank_wide import rank_wide
    
    sample_tickets = [
        {"id": "T1", "text": "Can I get help updating our billing email address?"},
        {"id": "T2", "text": "CRITICAL EMERGENCY: Database crashed with 500 error, all systems halted!"},
    ]
    
    ranked = rank_wide(sample_tickets)
    assert len(ranked) == 2
    # The critical emergency must rank first because escalate is True
    assert ranked[0]["id"] == "T2"
    assert ranked[0]["escalate"] is True
    assert ranked[1]["id"] == "T1"
    assert ranked[1]["escalate"] is False
