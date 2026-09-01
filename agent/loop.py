import json
import re
from llm.client import chat_with_tools
from tools.base import TOOL_FUNCTIONS, TOOL_SCHEMAS
from agent.state import AgentState #上下文管理


SYSTEM_PROMPT = """你是一个强大的本地编程智能体 (Coding Agent)。
你可以通过调用工具来读取文件、写入代码以及执行终端命令。
请遵循以下原则：
【一、 终端与环境安全】
1. 沙盒锁定：你的终端工作目录已永久锁定在项目根目录（workspace）。绝对禁止使用 cd 命令尝试切换目录！
2. 相对路径：如果需要操作或执行子目录下的文件，必须全程使用相对路径（例如写入 folder/config.json，执行 python folder/script.py 或 pytest folder/test.py）。

【二、 工具调用规范】
3. 严格匹配：调用工具时，必须严格使用工具描述中给定的参数名称（例如 run_command 必须使用 command 参数，绝不能使用 cmd）。
4. 格式严禁：你必须使用规范的 Tool Calling 机制调用工具！绝对禁止在普通文本回复中输出类似 <｜｜DSML｜｜> 或 XML 的原始标签！

【三、 开发与自测闭环】
5. 了解全貌：在修改代码前，尽量先用 read_file 或 list_directory 了解项目结构。
6. 测试驱动：在你完成核心业务代码的编写后，必须主动编写对应的测试脚本（如使用 pytest 的单元测试）。
7. 自主运行：代码和测试编写完毕后，必须使用 run_command 执行测试命令，验证你的代码。
8. 错误自愈：遇到报错时，仔细阅读终端返回的 stderr，自主分析错误原因，修改代码后再次运行测试，直到完全闭环。
9. 停止幻觉：如果你运行代码后发现没有任何报错输出，且自主阅读代码未发现明显逻辑漏洞，必须立即停止过度推理。

【四、 任务交付】
10. 只有当你确认任务已经完全闭环（代码写完、测试跑通、Bug 修复完毕）后，才向用户回复“任务已完成”并总结你的操作。
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
def run_agent(user_request: str, max_steps: int = 25):
   #上下文初始化
    #messages = [
    #    {"role": "system", "content": SYSTEM_PROMPT},
    #    {"role": "user", "content": user_request}
    #]
    state=AgentState(system_prompt=SYSTEM_PROMPT,user_request=user_request,max_steps=max_steps)
    
    #step = 0
    print(f"\n[Agent 启动]收到任务: {user_request}\n")


    while state.step_count < state.max_steps:
        state.step_count += 1
        print(f"---  Step {state.step_count} ---")
        print("思考中...")

        
        response_msg = chat_with_tools(state.messages, TOOL_SCHEMAS)
        
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

        
        state.add_message(response_msg)

        
        for tool_call in response_msg.tool_calls:
            function_name = tool_call.function.name
            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
                print(f"无法解析工具参数:{tool_call.function.arguments}")

            print(f"执行工具: {function_name}({arguments})")

            
            if function_name in TOOL_FUNCTIONS:
                tool_result = TOOL_FUNCTIONS[function_name](**arguments)
            else:
                tool_result = f"Error: 找不到名为{function_name}的工具"

            #截断过长的输出，防止Token爆炸
            if len(tool_result) > 2000:
                tool_result = tool_result[:2000] + "\n...[输出过长，已截断]"

            #将工具的执行结果封装成规范格式，追加回上下文
            state.add_message({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": str(tool_result)
            })

            print(f"工具返回结果 (长度 {len(str(tool_result))} 字符)")

    #循环终止条件2
    if state.step_count >= max_steps:
        print(f"\n达到最大执行步数限制 ({max_steps}步)，强制终止以防止死循环。")