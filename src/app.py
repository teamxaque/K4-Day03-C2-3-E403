"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv
import json
import re

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, lookup_order, check_return_policy, check_refund_eligibility, create_return_request
from prompts import CHATBOT_BASELINE_PROMPT, build_react_prompt, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")

def parse_action(text):
    final_match = re.search(r"Final Answer:\s*(.*)", text, re.S)
    if final_match:
        return "FINAL", final_match.group(1).strip()

    action_match = re.search(r"Action:\s*(\w+)", text)
    input_match = re.search(
        r"Action Input:\s*(\{.*\})",
        text,
        re.S
    )
    if not action_match:
        return None, None
        
    action = action_match.group(1)
    args = {}

    if input_match:
        try:
            args = json.loads(input_match.group(1))
        except json.JSONDecodeError:
            pass

    return action, args
    
def execute_tool(action, args):

    if action not in AVAILABLE_TOOLS:
        return f"Unknown tool: {action}"

    tool = AVAILABLE_TOOLS[action]

    try:
        result = tool(**args)
        return result

    except Exception as e:
        return f"Tool Error: {e}"


def run_react_agent(user_query, provider):
    history = []
    print("=" * 60)
    print("Question:")
    print(user_query)
    print("=" * 60)
    for step in range(MAX_ITERATIONS):
        print(f"\n------ Step {step+1} ------")
        prompt = build_react_prompt(
            user_query,
            history
        )
        response = provider.generate(prompt)
        # nếu provider trả object thì chuyển sang string
        if hasattr(response, "content"):
            llm_output = response.content
        else:
            llm_output = str(response)

        print(llm_output)

        action, args = parse_action(
            llm_output
        )
        if action is None:
            print("Không parse được Action.")
            break

        if action == "FINAL":
            print("\n===== FINAL ANSWER =====")
            print(args)
            return args
        observation = execute_tool(
            action,
            args
        )

        print("\nObservation")
        print(observation)

        history.append({
            "assistant": llm_output,
            "observation": observation

        })
    print("\nĐã vượt quá số bước.")

if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: ROLE 4: CORE AGENT DEVELOPER")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3
    sample_query = tests[7]["question"]
    
    # print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    # run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
