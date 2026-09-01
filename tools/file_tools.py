import os
from tools.base import register_tool
from pathlib import Path

#所有操作只能在当前目录下的workspace文件夹进行
WORKSPACE_DIR = Path(os.getcwd()) / "workspace"
WORKSPACE_DIR.mkdir(exist_ok=True)#若不存在则创建

#检查是否为非越权路径
def validate_path(file_path: str) -> Path:
    target_path = (WORKSPACE_DIR / file_path).resolve()
    #检查绝对路径，是否以WORKSPACE_DIR为前缀
    if not target_path.is_relative_to(WORKSPACE_DIR.resolve()):
        raise PermissionError(f"拦截：尝试越权访问！路径必须在{WORKSPACE_DIR.name}目录下。")
    return target_path

@register_tool(
    name="list_directory",
    description="列出指定目录下的所有文件和文件夹。了解项目结构时首先使用此工具。",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", 
                     "description": "相对路径，当前目录请传 '.'"}
        },
        "required": ["path"]
    }
)
def list_directory(path: str) -> str:
    try:
        safe_path = validate_path(path)
        if not safe_path.exists():
            return f"Error: 目录不存在 '{path}'"
        if not safe_path.is_dir():
            return f"Error: '{path}' 不是一个目录"
            
        items = os.listdir(safe_path)
        return f"目录 '{path}' 内容:\n" + "\n".join(items) if items else "空目录"
    except Exception as e:
        return f"Error: {str(e)}"

@register_tool(
    name="search_files",
    description="在工作区内通过关键字搜索包含该内容的文件名。",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string",
                         "description": "要搜索的代码片段或关键字"}
        },
        "required": ["keyword"]
    }
)
def search_files(keyword: str) -> str:
    # 遍历所有文件进行内容匹配
    matched_files = []
    for root, _, files in os.walk(WORKSPACE_DIR):
        for file in files:
            file_path = Path(root) / file
            try:
                content = file_path.read_text(encoding='utf-8')
                if keyword in content:
                    # 仅返回相对路径
                    matched_files.append(str(file_path.relative_to(WORKSPACE_DIR)))
            except UnicodeDecodeError:
                continue
                
    if not matched_files:
        return f"未找到包含关键字 '{keyword}' 的文件。"
    return "找到匹配的文件:\n" + "\n".join(matched_files)


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
        safe_path = validate_path(path)
        if not safe_path.exists():
            return f"Error: 路径不存在 '{path}'"

        if safe_path.is_dir():
            #如果是目录，返回目录内容
            return list_directory(path)
        
        return safe_path.read_text(encoding='utf-8')
    except Exception as e:
        return f"Error: {str(e)}"

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
        safe_path = validate_path(path)
        # 自动创建父目录
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(content, encoding='utf-8')
        return f"Success: 已成功写入 '{path}'"
    except Exception as e:
        return f"Error: {str(e)}"