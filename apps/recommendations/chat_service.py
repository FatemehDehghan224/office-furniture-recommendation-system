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


CHAT_STATE_FIELDS = {
    "person",
    "productType",
    "number_of_person",
    "budget",
    "budget_min",
    "budget_max",
    "style",
    "color",
    "fabric_material",
    "body_material",
}


def _strip_code_fence(value: str) -> str:
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", value.strip(), flags=re.IGNORECASE)


def _validate_model_payload(parsed: dict[str, Any]) -> dict[str, Any]:
    """Reject JSON that is valid syntactically but not part of the chat contract."""
    if "analysis_response" in parsed:
        if not isinstance(parsed["analysis_response"], str):
            raise InvalidModelResponse("analysis_response must be a string")
        return parsed

    required_fields = {"user_input", "llm_response", "success"}
    if not required_fields.issubset(parsed):
        raise InvalidModelResponse("Model response is missing required fields")
    if not isinstance(parsed["user_input"], dict):
        raise InvalidModelResponse("user_input must be an object")
    if set(parsed["user_input"]) != CHAT_STATE_FIELDS:
        raise InvalidModelResponse("user_input has an unexpected shape")
    if not isinstance(parsed["llm_response"], str):
        raise InvalidModelResponse("llm_response must be a string")
    if not isinstance(parsed["success"], bool):
        raise InvalidModelResponse("success must be a boolean")
    return parsed


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
    if not isinstance(raw_response, str):
        raise InvalidModelResponse("Model response must be text")
    try:
        parsed = json.loads(_strip_code_fence(raw_response))
    except (json.JSONDecodeError, TypeError) as error:
        raise InvalidModelResponse("Model response was not valid JSON") from error
    if not isinstance(parsed, dict):
        raise InvalidModelResponse("Model response must be a JSON object")
    return _validate_model_payload(parsed)
