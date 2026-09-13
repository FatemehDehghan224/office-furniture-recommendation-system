import json
from services.run_flow import run_recommender

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", "-p", required=True, help="Path to hierarchical products JSON")
    parser.add_argument("--use-llm", action="store_true", help="If set, use LLM for user collection (requires call_llm implementation)")
    parser.add_argument("--topk", type=int, default=5)
    args = parser.parse_args()

    out = run_recommender(args.products, use_llm=args.use_llm, top_k=args.topk)
    print(json.dumps(out, ensure_ascii=False, indent=2))