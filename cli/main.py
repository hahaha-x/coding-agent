from agent.loop import run_agent
import sys

def get_multiline_input():
    print("=====================================")
    print("||      Coding Agent Terminal      ||")
    print("=====================================")
    print("提示：回车为换行，ctrl+z为输入结束")
    print("请输入任务指令：")

    
    try:
        user_input=sys.stdin.read().strip()
        return user_input
    except KeyboardInterrupt:
        print("用户中止输入")
        sys.exit(0)


if __name__ == "__main__":
    print("=====================================")
    print("||      Coding Agent Terminal      ||")
    print("=====================================")
    
    # 模拟用户的任务指令
    task=get_multiline_input()

    if not task:
        print("任务指令为空，退出系统")
        sys.exit(1)
    
    run_agent(task)