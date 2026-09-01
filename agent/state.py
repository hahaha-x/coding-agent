class AgentState:
    def __init__(self, system_prompt: str, user_request: str, max_steps: int = 15):
        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request}
        ]
        self.step_count = 0
        self.max_steps = max_steps
        self.modified_files = set()

    def add_message(self, message):
        self.messages.append(message)
        self._compress_context()

    def _compress_context(self):
        #压缩上下文，仅保留最初2条（人设和初始任务），和最近10条交互信息
        #问题：工具执行结果和大模型调用工具命令两条消息绑定，只保留10条会导致把tool_calls丢掉
        if len(self.messages) > 20:
            #self.messages = self.messages[:2] + self.messages[-10:]
            core_messages = self.messages[:2]
            recent_messages = self.messages[-10:]
            #若tool_calls切掉了，把对应工具执行结果也切掉
            while recent_messages:
                first_msg = recent_messages[0]
                #可能是字典/对象
                if isinstance(first_msg, dict):
                    role = first_msg.get("role")
                else:
                    role = getattr(first_msg, "role", None)
                
                # 如果第一条是被切断的 tool 结果，则将其抛弃
                if role == "tool":
                    recent_messages.pop(0)
                else:
                    break
            self.messages = core_messages + recent_messages
            print("【上下文压缩处理】上下文过长，已自动压缩历史记录。")