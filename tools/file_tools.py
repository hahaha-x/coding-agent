import os
from tools.base import register_tool

@register_tool(
    name="read_file",
    description="读取指定路径的文件内容。如果给定的是目录，将返回该目录下的文件列表。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "要读取的文件或目录的相对或绝对路径。"
            }
        },
        "required": ["path"]
    }
)
def read_file(path: str) -> str:
    try:
        if not os.path.exists(path):
            return f"Error: 路径不存在 '{path}'"

        if os.path.isdir(path):
            #如果是目录，返回目录内容
            files = os.listdir(path)
            if not files:
                return f"'{path}' 是一个空目录。"
            return f"'{path}' 是一个目录。包含以下内容: \n" + "\n".join(files)

        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error 读取文件时发生错误: {str(e)}"

@register_tool(
    name="write_file",
    description="将内容写入指定文件。如果文件存在，将完全覆盖原内容；如果所在目录不存在，将自动创建目录。",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "要写入的文件路径。"
            },
            "content": {
                "type": "string",
                "description": "要写入的文件完整内容。"
            }
        },
        "required": ["path", "content"]
    }
)
def write_file(path: str, content: str) -> str:
    try:
        dir_name = os.path.dirname(os.path.abspath(path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: 已成功将内容写入 '{path}'"
    except Exception as e:
        return f"Error 写入文件时发生错误: {str(e)}"