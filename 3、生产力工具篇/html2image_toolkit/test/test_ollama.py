import requests
import json

# Ollama 服务地址（本地默认）
OLLAMA_URL = "http://localhost:11434/api/generate"
CHAT_URL = "http://localhost:11434/api/chat"

# 1. 非流式单次对话（适合短文本、快速获取结果）
def non_stream_generate(prompt):
    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False,
        "temperature": 0.7,  # 温度（0-1，越低越确定，越高越有创意）
        "max_tokens": 1024   # 最大生成 tokens 数
    }
    response = requests.post(OLLAMA_URL, json=data)
    response.raise_for_status()  # 抛出请求错误
    result = response.json()
    print("非流式结果：", result["response"])
    return result["response"]

# 2. 流式对话（适合长文本、实时展示）
def stream_generate(prompt):
    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": True,
        "temperature": 0.7
    }
    print("流式结果：", end="")
    with requests.post(OLLAMA_URL, json=data, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_lines():
            if chunk:
                chunk_data = json.loads(chunk.decode("utf-8"))
                if "response" in chunk_data:
                    print(chunk_data["response"], end="", flush=True)
                if chunk_data.get("done"):  # 结束标志
                    break
    print("\n")

# 3. 多轮对话（保留上下文，用 chat 接口）
def multi_turn_chat():
    messages = []  # 存储对话历史（role: user/assistant，content: 内容）
    while True:
        user_input = input("你：")
        if user_input in ["退出", "q"]:
            break
        # 追加用户消息到历史
        messages.append({"role": "user", "content": user_input})
        data = {
            "model": "qwen3:8b",
            "messages": messages,
            "stream": False,
            "temperature": 0.7
        }
        response = requests.post(CHAT_URL, json=data)
        response.raise_for_status()
        result = response.json()
        assistant_msg = result["message"]["content"]
        print("qwen3：", assistant_msg)
        # 追加助手回复到历史（保留上下文）
        messages.append({"role": "assistant", "content": assistant_msg})

# 测试调用
if __name__ == "__main__":
    non_stream_generate("解释什么是大语言模型")
    stream_generate("用3句话介绍 qwen3 模型")
    multi_turn_chat()