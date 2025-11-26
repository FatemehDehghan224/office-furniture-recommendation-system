import os
import json
import re
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from models.sofa_model import UserRequest
from recommend.recommender import recommend_products
from utils.decorator import retry_on_failure
from utils.loader import load_products
from utils.utils import load_system_prompt, entry_to_json

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

chat_history = []

@retry_on_failure(max_retries=3, initial_delay=2, backoff_factor=2)
def input_collector() -> dict:
    """
    Collect user furniture preferences, generate recommendations,
    store them in model memory (chat_history), and return final structured result.
    """
    prompt_path = "../agents/prompts/input_collector_prompt.txt"
    system_prompt = load_system_prompt(prompt_path)

    llm = ChatOpenAI(
        api_key=api_key,
        model="gpt-4o",
        temperature=0.0,
        base_url="https://api.avalai.ir/v1",
        verbose=True,
    )

    collected_fields = {
        "person": None,
        "productType": None,
        "number_of_person": None,
        "budget": None,
        "budget_min": None,
        "budget_max": None,
        "style": None,
        "color": None,
        "fabric_material": None,
        "body_material": None
    }

    print("سلام! قراره با هم یه مبلمان مناسب برای شما پیدا کنیم. لطفاً جواب سؤالات رو بده. هر وقت سوالی داشتی هم می‌تونی از من بپرسی.")

    result = {}

    while True:
        user_input_text = input("You: ")

        history_text = "\n".join(
            [f"User: {h['user_input']}\nAI: {h['llm_response']}" for h in chat_history]
        )

        # گرفتن آخرین recommendation ها
        latest_recs = None
        for h in reversed(chat_history):
            if "recommendations" in h and h["recommendations"]:
                latest_recs = h["recommendations"]
                break

        escaped_system_prompt = system_prompt.replace("{", "{{").replace("}", "}}")
        escaped_history = history_text.replace("{", "{{").replace("}", "}}")
        escaped_recommendations = ""
        if latest_recs:
            escaped_recommendations = json.dumps(latest_recs, ensure_ascii=False, indent=2)
            escaped_recommendations = escaped_recommendations.replace("{", "{{").replace("}", "}}")

        dynamic_template = f"""{escaped_system_prompt}
                                Conversation so far:
                                {escaped_history}

                                Previous Recommendations:
                                {escaped_recommendations}

                                User input: {{user_input}}"""

        prompt = PromptTemplate(
            template=dynamic_template,
            input_variables=["user_input"]
        )

        chain = prompt | llm
        invoke_result = chain.invoke({"user_input": user_input_text})

        if hasattr(invoke_result, "content"):
            response_text = invoke_result.content
        elif isinstance(invoke_result, str):
            response_text = invoke_result
        elif isinstance(invoke_result, dict) and "text" in invoke_result:
            response_text = invoke_result["text"]
        else:
            response_text = str(invoke_result)

        response_text = re.sub(r"^```json\s*|\s*```$", "", response_text.strip())

        try:
            parsed = json.loads(response_text)
            if parsed is None or not isinstance(parsed, dict):
                parsed = {}

            is_analysis_mode = "analysis_response" in parsed

            if is_analysis_mode:
                result = {
                    "user_input": collected_fields,
                    "llm_response": parsed.get("analysis_response", "No response from LLM."),
                    "thoughts": parsed.get("thoughts", "No thoughts provided."),
                    "success": False,
                    "is_analysis": True
                }
            else:
                user_input_parsed = parsed.get("user_input") or {}
                for key in collected_fields:
                    if key in user_input_parsed and user_input_parsed[key] is not None:
                        collected_fields[key] = user_input_parsed[key]

                result = {
                    "user_input": collected_fields,
                    "llm_response": parsed.get("llm_response", "No response from LLM."),
                    "thoughts": parsed.get("thoughts", "No thoughts provided."),
                    "success": parsed.get("success", False),
                    "is_analysis": False
                }

        except json.JSONDecodeError:
            result = {
                "user_input": collected_fields,
                "llm_response": "متاسفم، خروجی JSON معتبر نبود. لطفاً یک پاسخ کوتاه و واضح بده.",
                "thoughts": "JSON parse failed.",
                "success": False,
                "is_analysis": False
            }

        print("LLM:", result["llm_response"])
        print("response: ", result)

        chat_history.append({
            "user_input": user_input_text,
            "llm_response": result["llm_response"],
            "thoughts": result["thoughts"],
            "recommendations": latest_recs
        })

        if result.get("success") and not result.get("is_analysis"):
            print("\n✅ همه اطلاعات ضروری جمع‌آوری شد!")
            break

    products = load_products()
    user_request = UserRequest(**collected_fields)
    recommendations = recommend_products(user_request, products)
    json_recommendations = [entry_to_json(p) for p in recommendations]

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
