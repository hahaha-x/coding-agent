import json

#存储函数名和对应Python函数
TOOL_FUNCTIONS = {}

#可用工具
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