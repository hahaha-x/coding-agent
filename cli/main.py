from agent.loop import run_agent

if __name__ == "__main__":
    print("=====================================")
    print("||      Coding Agent Terminal      ||")
    print("=====================================")
    
    # 模拟用户的任务指令
    task = "请在当前目录下创建一个名为 hello.py 的文件，里面写一段 Python 代码：打印 'Hello World'。创建完毕后，请帮我执行这个文件，确认它能正常输出。"
    
    run_agent(task)