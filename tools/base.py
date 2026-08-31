import json

# 工具注册字典，用来存储函数名和对应的真实Python函数
TOOL_FUNCTIONS = {}

# 工具 Schema 列表，用来发给大模型告诉它有哪些工具可用
TOOL_SCHEMAS = []

def register_tool(name, description, parameters):
    
    def decorator(func):
        TOOL_FUNCTIONS[name] = func
        TOOL_SCHEMAS.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters
            }
        })
        return func
    return decorator