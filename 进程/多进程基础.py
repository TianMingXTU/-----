"""
如果说“多线程”是同一家餐厅里的几个服务员（共享同一个厨房和食材），那么“多进程”就是直接在隔壁开了一家一模一样的分店。

核心逻辑：当你启动一个子进程时，操作系统会把你当前的 Python 环境完整克隆一份。
代价与收益：创建进程非常耗费资源（开分店很贵），但好处是它们拥有完全独立的内存空间。一个进程崩了，另一个毫发无损；一个进程修改了全局变量，另一个进程里的变量连一根汗毛都不会变。
🛠️ 核心语法结构
在 Python 中，使用 multiprocessing 模块。记住这三个核心动作：

实例化：p = Process(target=你要执行的函数名, args=(传给函数的参数元组,))
点火启动：p.start() （告诉操作系统去开分店吧，主进程继续往下走）
阻塞等待：p.join() （主进程停在这里，等这家分店倒闭/执行完，再往下走）
⚠️ 工业级红线（语法天坑）：
在 Windows 系统下写多进程，必须把执行逻辑放在 if __name__ == "__main__": 下面。否则它在克隆分店的时候，会无限套娃克隆，直接把电脑卡死。
"""

# ================= 1. 依赖导入 =================
import multiprocessing
import time

# ================= 2. 全局状态 =================
MAGIC_NUMBER = 0


def child_process_work(process_name: str):
    """
    这是子进程要执行的任务。
    它会尝试修改全局变量。
    """
    global MAGIC_NUMBER
    print(f"[{process_name}] 刚启动时，看到的 MAGIC_NUMBER 是: {MAGIC_NUMBER}")

    # 子进程大笔一挥，修改了全局变量
    MAGIC_NUMBER = 100
    print(f"[{process_name}] 经过修改，现在的 MAGIC_NUMBER 是: {MAGIC_NUMBER}")

    # 模拟耗时操作
    time.sleep(1)
    print(f"[{process_name}] 执行完毕，即将退出。")


# ================= 3. 刻意练习骨架 =================
def main():
    global MAGIC_NUMBER
    print(f"[主进程] 启动！当前的 MAGIC_NUMBER 是: {MAGIC_NUMBER}")

    # TODO 1: 实例化一个子进程对象 (Process)
    # 要求：让它执行 child_process_work 函数，并传入参数 "Worker-1"
    # p = ...
    p = multiprocessing.Process(target=child_process_work, args=("Worker-1",))

    # TODO 2: 点火启动这个子进程
    # ...
    p.start()

    # TODO 3: 让主进程在这里挂起等待，直到子进程执行完毕
    # ...
    p.join()

    # 终极见证时刻：
    print(f"[主进程] 子进程已经执行完了。")
    print(f"[主进程] 让我来看看现在的 MAGIC_NUMBER 是多少: {MAGIC_NUMBER}")


# 必须写在 __main__ 防护罩下
if __name__ == "__main__":
    main()
