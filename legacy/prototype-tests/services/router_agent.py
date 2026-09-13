import json
from typing import Optional, Dict, Any
from pydantic import ValidationError
from tests.model.models import UserRequest, UserType, ProductType, Style, Color, FabricMaterial, BodyMaterial

def call_llm(prompt: str, system: Optional[str] = None, model: str = "gpt-4o-mini") -> str:
    """
    Placeholder/abstraction for LLM call.
    - Replace body with your OpenAI (or other) client call.
    - IMPORTANT: This function should *return text* — ideally a JSON string matching UserRequest.
    Example with OpenAI (commented):

    import openai
    openai.api_key = "..."
    resp = openai.ChatCompletion.create(
        messages=[
            {"role":"system","content": system or "You are a helpful assistant."},
            {"role":"user","content": prompt}
        ],
        temperature=0.0
    )
    return resp.choices[0].message.content

    For now this function raises NotImplementedError so you remember to implement.
    """
    raise NotImplementedError("call_llm() is a placeholder. Implement LLM client call here.")


def llm_collect_user_input_via_prompt(schema: UserRequest, model_name: str = "gpt-4o-mini") -> Dict[str, Any]:
    """
    Build a prompt for the LLM so it asks user step-by-step and returns a JSON object
    matching the UserRequest fields. We instruct the models to always output VALID JSON only.
    """

    # Build choices metadata from enums to include in prompt
    def enum_values(e):
        return [m.value for m in e] if hasattr(e, "__members__") else []

    choices = {
        "person": enum_values(UserType),
        "productType": enum_values(ProductType),
        "style": enum_values(Style),
        "color": enum_values(Color),
        "fabric_material": enum_values(FabricMaterial),
        "body_material": enum_values(BodyMaterial),
    }

    prompt = f"""
You are a question-asking assistant. Your job: ask the user the minimum set of questions required to fill a JSON object matching this schema:

UserRequest fields:
- person (required): one of {choices['person']}
- productType (required): one of {choices['productType']}
- number_of_person (required): integer (e.g., 1,2,3)
- budget (required): integer budget in same currency as products
- style (optional): one of {choices['style']} or null
- color (optional): one of {choices['color']} or null
- fabric_material (optional): one of {choices['fabric_material']} or empty string
- body_material (optional): one of {choices['body_material']} or empty string

Constraints:
- Ask questions in Persian (Farsi) so the user understands.
- Only ask as many questions as needed; if user answers implicitly (e.g., says 'I want a manager desk'), parse it.
- When you have enough info, output a single JSON object EXACTLY matching the keys of UserRequest:
Example output:
{{"person": "manager", "productType": "office desk", "number_of_person": 1, "budget": 5000000, "style": "modern", "color": "black", "fabric_material": "", "body_material": "wood"}}

Important:
- Output ONLY the JSON when done (no extra words).
- If a field is unknown or user says 'no preference', use null for optional fields and for fabric/body use empty string "".

Begin conversation with user questions in Persian to collect these fields.
"""
    # call LLM to conduct the interactive session and return JSON string
    response_text = call_llm(prompt, system="You are a helpful Persian-speaking assistant.", model=model_name)
    # expected: JSON string
    try:
        parsed = json.loads(response_text)
    except Exception as e:
        raise ValueError(f"LLM did not return valid JSON. raw: {response_text[:300]} -- error: {e}")
    # validate using pydantic
    try:
        user_req = UserRequest.parse_obj(parsed)
    except ValidationError as e:
        raise ValueError(f"LLM returned JSON but failed validation: {e}")
    return user_req.model_dump()