"""Small OpenAI-compatible client used by the conversational agents.

Keeping provider configuration in one place makes the recommendation logic
independent from the LLM library. AvalAI exposes an OpenAI-compatible API.
"""

from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

BASE_URL = "https://api.avalai.ir/v1"


class LLMConfigurationError(ValueError):
    """Raised when the conversational provider cannot be configured."""


def ask_model(system_prompt: str, user_prompt: str, *, model: str, temperature: float) -> str:
    """Send one chat-completion request and return its text content."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMConfigurationError(
            "OPENAI_API_KEY تنظیم نشده است. مقدار آن را در recommendation/.env قرار دهید."
        )

    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
