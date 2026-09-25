"""Laya CoreML Agent wrapper for Jev-style typed decisions."""

import os
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import laya_coreml as laya

_CACHED_AGENT = None
_CACHED_MODEL_PATH = None


def find_model_path(preferred_path: Optional[str] = None) -> str:
    """Find local model folder or fallback to Hugging Face model id."""
    candidates = [
        preferred_path,
        os.environ.get("LAYA_MODEL_PATH"),
        "./models/ane",
        "../models/ane",
        "models/ane",
        str(Path(__file__).resolve().parent / "models" / "ane"),
        str(Path(__file__).resolve().parent.parent / "models" / "ane"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_dir():
            return str(Path(candidate).resolve())
    return "aac6fef/laya-multilingual-coreml-ane"


def get_agent(model_path: Optional[str] = None, local_files_only: Optional[bool] = None):
    """Load or return cached Laya CoreML agent."""
    global _CACHED_AGENT, _CACHED_MODEL_PATH
    target_path = find_model_path(model_path)
    
    if _CACHED_AGENT is not None and _CACHED_MODEL_PATH == target_path:
        return _CACHED_AGENT

    # If target_path is local dir, local_files_only can be True
    is_local_dir = Path(target_path).is_dir()
    if local_files_only is None:
        local_files_only = is_local_dir

    _CACHED_AGENT = laya.load(target_path, local_files_only=local_files_only)
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
                # noul is probability of True
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
    local_files_only: Optional[bool] = None,
) -> DecisionResult:
    """Make typed decisions from a state text/dict using Laya-CoreML.

    Args:
        state: Context text or dictionary state
        questions: Questions dict (choice, score, noul)
        model_path: Local path or HF repo ID (default: ANE model)
        local_files_only: Require local files only (default: True for local folders)

    Returns:
        DecisionResult dict with values, probabilities, and usage.
    """
    agent = get_agent(model_path=model_path, local_files_only=local_files_only)
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
