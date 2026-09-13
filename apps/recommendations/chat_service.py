import json
import os
import re
from pathlib import Path
from typing import Any

from recommendation.utils.llm_client import ask_model
from recommendation.utils.utils import load_system_prompt


PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "recommendation"
    / "agents"
    / "prompts"
    / "input_collector_prompt.txt"
)


class InvalidModelResponse(ValueError):
    """Raised when the conversational model does not return the agreed JSON shape."""


def _strip_code_fence(value: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.IGNORECASE)


def collect_chat_turn(
    message: str,
    *,
    state: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Convert one Persian chat turn into the existing structured request contract."""
    system_prompt = load_system_prompt(str(PROMPT_PATH))
    context = {
        "current_user_input": state or {},
        "recent_history": (history or [])[-20:],
        "latest_message": message,
    }
    raw_response = ask_model(
        system_prompt,
        json.dumps(context, ensure_ascii=False),
        model=os.getenv("LLM_INPUT_MODEL", "gpt-4o"),
        temperature=0.0,
    )
    try:
        parsed = json.loads(_strip_code_fence(raw_response))
    except (json.JSONDecodeError, TypeError) as error:
        raise InvalidModelResponse("Model response was not valid JSON") from error
    if not isinstance(parsed, dict):
        raise InvalidModelResponse("Model response must be a JSON object")
    return parsed
