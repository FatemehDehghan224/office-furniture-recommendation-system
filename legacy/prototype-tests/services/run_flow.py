from typing import Dict, Any
from tests.services.handler import cli_collect_user_input
from tests.services.router_agent import llm_collect_user_input_via_prompt
from tests.services.rule_engine import RuleEngine
from tests.model.models import UserRequest
from tests.utils.load_product import load_hierarchical_products


def run_recommender(products_json_path: str,
                    use_llm: bool = False,
                    llm_model_name: str = "gpt-4o-mini",
                    top_k: int = 5) -> Dict[str, Any]:
    """
    Main entry:
    - loads products
    - collects user input via LLM (if use_llm) or CLI fallback
    - runs RuleEngine and returns recommendations
    """
    products = load_hierarchical_products(products_json_path)
    # collect user request
    if use_llm:
        # LLM should conduct interactive Q&A and return JSON (see llm_collect_user_input_via_prompt)
        user_dict = llm_collect_user_input_via_prompt(UserRequest, model_name=llm_model_name)
    else:
        user_dict = cli_collect_user_input()

    user_req = UserRequest.parse_obj(user_dict)
    engine = RuleEngine(products)
    recs = engine.recommend(user_req, top_k=top_k)
    result = {
        "user_request": user_req.model_dump(),
        "recommendations": recs
    }
    return result