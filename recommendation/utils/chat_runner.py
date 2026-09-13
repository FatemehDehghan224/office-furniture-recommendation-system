from recommendation.agents.input_collector_agent import input_collector, chat_history, reset_chat_history
from recommendation.agents.text_generator_agent import generate_recommendation_text

chat_memory = []

def run_chat(reset_memory: bool = True):
    global chat_memory

    if reset_memory:
        chat_memory = []
        reset_chat_history()

    collected = input_collector()
    if not collected:
        print("⚠️ ارتباط با مدل برقرار نشد. لطفاً بعداً دوباره تلاش کنید.")
        return

    user_input = collected["user_input"]
    recommendations = collected["recommendations"]

    print("\n✅ User input نهایی:")
    print(user_input)

    print("\n🎯 پیشنهادات برتر:")
    for r in recommendations:
        print(r)

    text_output = generate_recommendation_text(recommendations)
    if not text_output:
        text_output = "⚠️ خطایی در تولید متن رخ داد. لطفاً بعداً دوباره تلاش کنید."

    print("\n📢 متن نهایی برای کاربر:")
    print(text_output)

    chat_memory.append({"user": user_input, "response": text_output})

def menu_loop():
    while True:
        print("\n=== منو ===")
        print("1. شروع چت جدید")
        print("2. ادامه چت قبلی")
        print("3. نمایش تاریخچه حافظه")
        print("4. خروج")

        choice = input("گزینه مورد نظر را وارد کنید: ")

        if choice in ["1", "۱"]:
            run_chat(reset_memory=True)
        elif choice in ["2", "۲"]:
            if not chat_memory:
                print("❌ هیچ مکالمه‌ای برای ادامه وجود ندارد. از چت جدید شروع کنید.")
            else:
                run_chat(reset_memory=False)
        elif choice in ["3", "۳"]:
            if not chat_memory:
                print("📭 حافظه خالی است.")
            else:
                print("\n=== حافظه چت (chat_memory) ===")
                for idx, h in enumerate(chat_memory, 1):
                    print(f"{idx}. User Input: {h['user']}")
                    print(f"   Response: {h['response']}")
            if chat_history:
                print("\n=== حافظه مدل (chat_history) ===")
                for idx, h in enumerate(chat_history, 1):
                    print(f"{idx}. User: {h['user_input']}")
                    print(f"   LLM: {h['llm_response']}")
                    if h.get("recommendations"):
                        print("   → Recommendations:", h["recommendations"])
        elif choice in ["4", "۴"]:
            print("👋 پایان برنامه. خداحافظ!")
            break
        else:
            print("گزینه نامعتبر! دوباره تلاش کنید.")
