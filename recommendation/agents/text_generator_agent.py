import json
from pathlib import Path
from recommendation.utils.decorator import retry_on_failure
from recommendation.utils.llm_client import ask_model
from recommendation.utils.utils import load_system_prompt

BASE_DIR = Path(__file__).resolve().parent.parent
PROMPT_PATH = BASE_DIR / "agents" / "prompts" / "text_generator_prompt.txt"

system_prompt = load_system_prompt(str(PROMPT_PATH))

@retry_on_failure(max_retries=3, initial_delay=2, backoff_factor=2)
def generate_recommendation_text(products: list[dict]) -> str:
    """
    Generate a natural Persian description for recommended products.
    """
    products_json = json.dumps(products, ensure_ascii=False, indent=2)
    prompt_with_products = system_prompt.replace("{products_json}", products_json)
    return ask_model(
        prompt_with_products,
        "برای محصولات بالا، متن پیشنهادی فارسی تولید کن.",
        model="gpt-4o-mini",
        temperature=0.7,
    )
