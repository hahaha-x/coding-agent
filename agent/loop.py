import json
import re
from llm.client import chat_with_tools
from tools.base import TOOL_FUNCTIONS, TOOL_SCHEMAS


SYSTEM_PROMPT = """你是一个强大的本地编程智能体 (Coding Agent)。
你可以通过调用工具来读取文件、写入代码以及执行终端命令。
请遵循以下原则：
1. 在修改代码前，尽量先用 read_file 或 run_command(如 ls/dir) 了解项目结构。
2. 遇到报错时，仔细阅读 stderr，并自主分析原因，尝试修改代码后再次运行测试。
3. 只有当你确认任务已经完全闭环并且成功后，才向用户回复“任务已完成”并总结你的操作。
4. 【严重警告】：你必须使用规范的 Tool Calling 机制调用工具！绝对禁止在普通文本回复中输出类似 <｜｜DSML｜｜> 或 XML 的原始标签！
5. 【严格限制】：调用工具时，必须严格使用工具描述中给定的参数名称（例如 run_command 必须使用 command 参数，绝不能使用 cmd）。
"""

def fix_dsml(content: str):
    #利用正则提取泄露的底层调用标签
    if not content:
        return None
        
    #尝试匹配工具名称
    name_match = re.search(r'<｜｜DSML｜｜invoke name="([^"]+)"', content)
    if not name_match:
        return None
    tool_name = name_match.group(1)
    
    #尝试匹配所有参数
    args = {}
    param_matches = re.finditer(r'<｜｜DSML｜｜parameter name="([^"]+)"[^>]*>(.*?)</｜｜DSML｜｜parameter>', content, re.DOTALL)
    for m in param_matches:
        args[m.group(1)] = m.group(2).strip()
        
    #cmd 纠正为 command
    if tool_name == "run_command" and "cmd" in args:
        args["command"] = args.pop("cmd")
        
    
    class FakeToolCall:
        def __init__(self, name, arguments):
            self.id = f"call_fallback_{name}"
            self.function = type("FakeFunction", (), {"name": name, "arguments": json.dumps(args)})()
            
    return [FakeToolCall(tool_name, args)]


#agent loop
def run_agent(user_request: str, max_steps: int = 15):
   #上下文初始化
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_request}
    ]
    
    step = 0
    print(f"\n[Agent 启动]收到任务: {user_request}\n")


    while step < max_steps:
        step += 1
        print(f"---  Step {step} ---")
        print("思考中...")

        
        response_msg = chat_with_tools(messages, TOOL_SCHEMAS)
        
        #未使用工具则认为任务结束
        #if not response_msg.tool_calls:
        #    print("\n[最终回复]:")
        #    print(response_msg.content)
        #    break

        if not getattr(response_msg, 'tool_calls', None):
            
            fix_response = fix_dsml(response_msg.content)
            
            if fix_response:
                print("拦截到模型格式幻觉，已成功提取指令！")
                response_msg.tool_calls = fix_response
            else:
                print("\n[最终回复]:")
                print(response_msg.content)
                break

        
        messages.append(response_msg)

        
        for tool_call in response_msg.tool_calls:
            function_name = tool_call.function.name
            
            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
                print(f"无法解析工具参数:{tool_call.function.arguments}")

            print(f" 执行工具: {function_name}({arguments})")

            
            if function_name in TOOL_FUNCTIONS:
                tool_result = TOOL_FUNCTIONS[function_name](**arguments)
            else:
                tool_result = f"Error: 找不到名为{function_name}的工具"

            #截断过长的输出，防止Token爆炸
            if len(tool_result) > 2000:
                tool_result = tool_result[:2000] + "\n...[输出过长，已截断]"

            #将工具的执行结果封装成规范格式，追加回上下文
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_result)
            })

            print(f" 工具返回结果 (长度 {len(str(tool_result))} 字符)")

    #循环终止条件2
    if step >= max_steps:
        print(f"\n达到最大执行步数限制 ({max_steps}步)，强制终止以防止死循环。")