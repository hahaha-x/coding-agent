#临时测试文件 测试大模型连通性 llm->client.py

from llm.client import chat_with_tools

messages = [{"role": "user", "content": "你好，请用一句话证明你在线。"}]
response = chat_with_tools(messages)

print("大模型回复:", response.content)
