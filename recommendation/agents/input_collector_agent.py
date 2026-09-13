"""Input collector agent: interactively collect user requirements,
call LLM for extraction/clarification, run recommender and return JSON recommendations.

Assumptions:
- `load_system_prompt(path)` returns string prompt content.
- `recommend_products(user_request, products)` exists and returns product objects.
- `UserRequest` is a pydantic/dataclass-like model that accepts collected fields.
- `retry_on_failure` decorator is available and works as expected.
"""

from __future__ import annotations
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List

from recommendation.models.sofa_model import UserRequest
from recommendation.recommend.recommender import recommend_products
from recommendation.utils.decorator import retry_on_failure
from recommendation.utils.llm_client import ask_model
from recommendation.utils.loader import load_products
from recommendation.utils.utils import load_system_prompt, entry_to_json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROMPT_PATH = PROJECT_ROOT / "agents" / "prompts" / "input_collector_prompt.txt"

chat_history: List[Dict[str, Any]] = []


def _safe_extract_text(llm_result: Any) -> str:
    """
    Normalize possible LLM return formats into a plain string.
    Handles: LLMResult-like objects, direct string, dict with 'text' or 'content'.
    """
    if llm_result is None:
        return ""
    try:
        if hasattr(llm_result, "content"):
            return str(llm_result.content)
        if isinstance(llm_result, dict):
            for k in ("text", "content", "output_text", "output"):
                if k in llm_result and llm_result[k] is not None:
                    return str(llm_result[k])
            return json.dumps(llm_result, ensure_ascii=False)
        if isinstance(llm_result, str):
            return llm_result
    except Exception as e:
        print('ERROR:', e)
    return str(llm_result)


def _clean_json_like_text(text: str) -> str:
    """
    Remove triple-backtick fences and surrounding whitespace commonly present in LLM outputs.
    """
    if not text:
        return ""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    return cleaned


@retry_on_failure(max_retries=3, initial_delay=2, backoff_factor=2)
def input_collector(prompt_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Interactive loop: collect user answers step-by-step, ask clarifying questions via LLM,
    stop when success==True and required fields are filled. Returns a dict with
    'user_input' and 'recommendations' (list of JSON entries).
    """
    if prompt_path is None:
        prompt_path = DEFAULT_PROMPT_PATH
    if not Path(prompt_path).exists():
        logger.error("Prompt file not found: %s", prompt_path)
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    system_prompt = load_system_prompt(str(prompt_path))

    collected_fields: Dict[str, Optional[Any]] = {
        "person": None,
        "productType": None,
        "number_of_person": None,
        "budget": None,
        "budget_min": None,
        "budget_max": None,
        "style": None,
        "color": None,
        "fabric_material": None,
        "body_material": None,
    }

    print("سلام! قراره با هم یه مبلمان مناسب برای شما پیدا کنیم. لطفاً جواب سؤالات رو بدید. هر وقت سوالی داشتید می‌تونید بپرسید.")

    while True:
        try:
            user_input_text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nتعامل قطع شد.")
            return {"user_input": collected_fields, "recommendations": []}

        history_text = "\n".join(
            f"User: {h.get('user_input')}\nAI: {h.get('llm_response')}" for h in chat_history
        )

        latest_recs = None
        for h in reversed(chat_history):
            if h.get("recommendations"):
                latest_recs = h["recommendations"]
                break

        recommendations_text = ""
        if latest_recs:
            try:
                recommendations_text = json.dumps(latest_recs, ensure_ascii=False, indent=2)
            except Exception:
                recommendations_text = str(latest_recs)

        user_prompt = (
            "Conversation so far:\n"
            f"{history_text}\n\n"
            "Previous Recommendations:\n"
            f"{recommendations_text}\n\n"
            f"User input: {user_input_text}"
        )
        response_text = ask_model(
            system_prompt,
            user_prompt,
            model="gpt-4o",
            temperature=0.0,
        )
        response_text = _clean_json_like_text(response_text)

        result = {
            "user_input": collected_fields.copy(),
            "llm_response": "متاسفانه پاسخی دریافت نشد.",
            "thoughts": "no reasoning produced",
            "success": False,
            "is_analysis": False,
        }

        try:
            parsed = json.loads(response_text) if response_text else {}
            if not isinstance(parsed, dict):
                parsed = {}

            if "analysis_response" in parsed:
                result.update({
                    "llm_response": parsed.get("analysis_response", "No response from LLM."),
                    "thoughts": parsed.get("thoughts", "No thoughts provided."),
                    "success": False,
                    "is_analysis": True,
                })
            else:
                user_input_parsed = parsed.get("user_input") or {}
                for key in collected_fields.keys():
                    if key in user_input_parsed and user_input_parsed[key] is not None:
                        collected_fields[key] = user_input_parsed[key]

                result.update({
                    "user_input": collected_fields.copy(),
                    "llm_response": parsed.get("llm_response", "No response from LLM."),
                    "thoughts": parsed.get("thoughts", "No thoughts provided."),
                    "success": bool(parsed.get("success", False)),
                    "is_analysis": False,
                })
        except json.JSONDecodeError:
            result.update({
                "llm_response": "متاسفم، خروجی JSON معتبر نبود. لطفاً یک پاسخ کوتاه و واضح بده.",
                "thoughts": "JSON parse failed.",
                "success": False,
                "is_analysis": False,
            })

        print("LLM:", result["llm_response"])
        logger.debug("Intermediate result: %s", result)

        chat_history.append({
            "user_input": user_input_text,
            "llm_response": result["llm_response"],
            "thoughts": result.get("thoughts"),
            "recommendations": latest_recs,
        })

        if result.get("success") and not result.get("is_analysis"):
            print("\n همه اطلاعات ضروری جمع‌آوری شد!")
            break

    products = load_products()
    user_request = UserRequest(**collected_fields)
    recommendations = recommend_products(user_request, products)
    json_recommendations = [entry_to_json(p) for p in recommendations]

    if chat_history:
        chat_history[-1]["recommendations"] = json_recommendations

    chat_history.append({
        "user_input": "[SYSTEM] Recommendations generated",
        "llm_response": "These are the recommended products.",
        "recommendations": json_recommendations
    })

    return {
        "user_input": collected_fields,
        "recommendations": json_recommendations,
    }


def reset_chat_history() -> None:
    """Clear the agent history before a genuinely new conversation."""
    chat_history.clear()
