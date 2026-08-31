import os
from openai import OpenAI
from dotenv import load_dotenv

#加载配置
load_dotenv()

#初始化
client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL")
)

MODEL_NAME = os.getenv("LLM_MODEL")

#与大模型对话，接受上下文，返回相应消息
def chat_with_tools(messages, tools=None):

    # 构造请求参数
    kwargs = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.1, 
    }

    
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    
    response = client.chat.completions.create(**kwargs)
    
    return response.choices[0].message