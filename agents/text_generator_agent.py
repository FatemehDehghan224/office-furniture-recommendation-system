import json
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from utils.decorator import retry_on_failure
from utils.utils import load_system_prompt


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

system_prompt = load_system_prompt("../agents/prompts/text_generator_prompt.txt")

llm = ChatOpenAI(
    api_key=api_key,
    model="gpt-4o-mini",
    temperature=0.7,
    base_url="https://api.avalai.ir/v1"
)

prompt = PromptTemplate(
    template=f"""{system_prompt}

Products JSON:
{{products_json}}""",
    input_variables=["products_json"]
)

chain = prompt | llm

@retry_on_failure(max_retries=3, initial_delay=2, backoff_factor=2)
def generate_recommendation_text(products: list[dict]) -> str:
    """
    Take a list of product dicts (from products_to_json)
    and return a nice Persian description.
    """
    products_json = json.dumps(products, ensure_ascii=False, indent=2)
    response = chain.invoke({"products_json": products_json})
    return response.content if hasattr(response, "content") else str(response)
