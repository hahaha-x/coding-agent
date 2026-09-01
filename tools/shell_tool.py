import subprocess
from tools.base import register_tool
import os
from pathlib import Path
from tools.file_tools import WORKSPACE_DIR
import re


CMD_PREFIX = r"(?:^|&&|\|\||;|\|)\s*"
#有风险的命令->规则
RISK_RULES = [
    #创建文件/文件夹
    {
        "pattern": CMD_PREFIX + r"mkdir\s+(?:-[a-zA-Z]+\s+)*(.+)",
        "message": "尝试创建新目录：{0}"
    },
    {
        "pattern": CMD_PREFIX + r"touch\s+(.+)",
        "message": "尝试创建新文件：{0}"
    },
    {
        "pattern": r">+\s*(?!&[12]\b)([^\s]+)", 
        "message": "尝试通过重定向写入或创建文件：{0}"
    },
    
    #删除
    {
        "pattern": CMD_PREFIX + r"rm\s+(?:-[a-zA-Z]+\s+)*(.+)",
        "message": "危险！尝试删除文件或目录：{0}"
    },
    
    #禁止退到上级/cd
    {
        "pattern": r"\.\.[/\\]",
        "message": "警告！检测到'../'，尝试跳出当前工作区沙箱。"
    },
    {
        "pattern": CMD_PREFIX + r"cd\s+(.+)",
        "message": "尝试使用cd命令切换目录至：{0}（已被系统提示词禁止）。"
    },
    
    #进行提权/kill
    {
        "pattern": CMD_PREFIX + r"sudo\s+(.+)",
        "message": "严重警告！尝试使用sudo提权执行：{0}"
    },
    {
        "pattern": CMD_PREFIX + r"(?:kill|pkill)\s+(.+)",
        "message": "警告！尝试终止进程：{0}"
    }
]


#用户检查指令是否要执行
def check_command_risk(command: str) -> tuple[bool, str]:
    for rule in RISK_RULES:
        match = re.search(rule["pattern"], command)
        if match:
            groups = match.groups()
            target = groups[0].strip() if groups else "未知目标"
            explanation = rule["message"].format(target)
            return True,explanation
            
    return False,"安全"


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
    is_risky, reason = check_command_risk(command)
    if is_risky:
        print(f"\n【提示】Agent试图执行命令'{command}'")
        print(f"       操作意图：{reason}")

        a=0
        while a<10:

            user_permission = input("\n是否允许执行以上操作?[Y/N]：").strip().lower()
            if user_permission in ['y', 'yes']:
                print("【提示】用户授权执行\n")
                break
            elif user_permission in ['n', 'no']:

                return f"Error: 用户拒绝了此操作，因为该命令被判定为高风险({reason})。请尝试使用其他安全方式完成任务。"
            else:
                print("输入错误！请输入 y或n。")
                a=a+1
        if a==10:
            print("输入错误超过10次，默认拒绝操作")
            return f"Error: 用户拒绝了此操作，因为该命令被判定为高风险({reason})。请尝试使用其他安全方式完成任务。"



    try:
        #防止大模型运行死循环或阻塞命令，timeout=15
        #subprocess.run无状态，命令结束临时终端销毁，会一直找文件
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',    #使用utf-8读取输出
            errors='replace',    #替换无法解码的词
            cwd=WORKSPACE_DIR,
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