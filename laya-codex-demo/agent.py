"""Laya MLX Agent wrapper for Jev-style typed decisions."""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import laya_mlx as laya

_CACHED_AGENT = None
_CACHED_MODEL_PATH = None


def find_model_path(preferred_path: Optional[str] = None) -> str:
    """Find local model folder or fallback to Hugging Face model id."""
    candidates = [
        preferred_path,
        os.environ.get("LAYA_MODEL_PATH"),
        "./models/mlx",
        "../models/mlx",
        "models/mlx",
        str(Path(__file__).resolve().parent / "models" / "mlx"),
        str(Path(__file__).resolve().parent.parent / "models" / "mlx"),
        "./models/ane",
        "../models/ane",
        "models/ane",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return str(Path(candidate).resolve())
    return "aac6fef/laya-multilingual-mlx"


def get_agent(model_path: Optional[str] = None):
    """Load or return cached Laya MLX agent."""
    global _CACHED_AGENT, _CACHED_MODEL_PATH
    target_path = find_model_path(model_path)
    
    if _CACHED_AGENT is not None and _CACHED_MODEL_PATH == target_path:
        return _CACHED_AGENT

    _CACHED_AGENT = laya.load(target_path)
    _CACHED_MODEL_PATH = target_path
    return _CACHED_AGENT


class DecisionResult(dict):
    """Result dictionary with easy access to simple values and raw details."""

    def __init__(self, raw: Dict[str, Any]):
        super().__init__()
        self.raw = raw
        self.answers = raw.get("answers", {})
        self.usage = raw.get("usage", {})
        self.values: Dict[str, Any] = {}

        for qid, ans in self.answers.items():
            qtype = ans.get("type")
            if qtype == "choice":
                val = ans.get("choice")
            elif qtype == "score":
                val = ans.get("score")
            elif qtype == "noul":
                val = bool(ans.get("noul", 0.0) >= 0.5)
            else:
                val = ans
            self.values[qid] = val
            self[qid] = val

        self["answers"] = self.answers
        self["usage"] = self.usage
        self["values"] = self.values


def decide(
    state: Union[str, Dict[str, Any]],
    questions: Dict[str, Dict[str, Any]],
    model_path: Optional[str] = None,
    **kwargs: Any,
) -> DecisionResult:
    """Make typed decisions from a state text/dict using Laya-MLX.

    Args:
        state: Context text or dictionary state
        questions: Questions dict (choice, score, noul)
        model_path: Local path or HF repo ID (default: MLX model)

    Returns:
        DecisionResult dict with values, probabilities, and usage.
    """
    agent = get_agent(model_path=model_path)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        raw = agent.predict(state, questions)
    return DecisionResult(raw)


# Helper builders for TypeSafe question schemas
def choice_question(instructions: str, criteria: Union[Dict[str, str], List[str]]) -> Dict[str, Any]:
    return {"type": "choice", "instructions": instructions, "criteria": criteria}


def score_question(instructions: str, criteria: List[str]) -> Dict[str, Any]:
    return {"type": "score", "instructions": instructions, "criteria": criteria}


def noul_question(instructions: str) -> Dict[str, Any]:
    return {"type": "noul", "instructions": instructions}
