import subprocess
from tools.base import register_tool

@register_tool(
    name="run_command",
    description="在当前终端执行 shell 命令或 Python 脚本，并返回执行结果 (stdout 和 stderr)。",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 shell 命令，例如 'python script.py' 或 'pytest'"
            }
        },
        "required": ["command"]
    }
)
def run_command(command: str) -> str:
    try:
        #防止大模型运行死循环或阻塞命令，timeout=15
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR 错误输出]:\n{result.stderr}"
            
        if not output.strip():
            return "Command executed successfully (no output)."
            
        return output
    except subprocess.TimeoutExpired:
        return "Error: 命令执行超时 (超过15秒被强制终止)。"
    except Exception as e:
        return f"Error 执行命令时发生异常: {str(e)}"