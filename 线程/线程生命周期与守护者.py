# ================= 0. 知识点与 API 映射 (快思考) =================
"""
【节点 1 & 2：线程生命周期与守护者 (Threading Lifecycle & Daemon)】

🧠 直觉模型：
主程序（MainThread）是一家公司的老板。
- `Thread(...)`：老板签发了一份劳务合同，但此时员工还没入职（并未在 OS 层面创建真正线程）。
- `start()`：员工正式入职，打卡干活。
- `join()`：老板在办公室死等（阻塞），直到这个员工把活干完，老板才下班。
- `daemon=True`（守护线程）：这就是公司的“背景音乐”或“保洁阿姨”。只要老板（主线程）一下班退出，不管保洁阿姨地有没有扫完，立刻被强制断电遣散。

🛠️ 核心 API 兵器谱：
- `threading.Thread(target, args, daemon)`
- `thread.start()`
- `thread.join(timeout)`
- `thread.is_alive()`
"""

# ================= 1. 依赖导入 (Imports) =================
import threading
import time
from typing import List, Dict

# ================= 2. API 实战场 (API Battleground) =================


def worker_task(task_name: str, cost_time: int) -> None:
    """模拟一个普通的工作任务"""
    print(f"👷 [Worker] {task_name} 开始工作，预计耗时 {cost_time} 秒...")
    time.sleep(cost_time)
    print(f"👷 [Worker] {task_name} 工作完成！")


def monitor_task() -> None:
    """模拟一个永远在后台轮询的监控任务"""
    print("👁️ [Monitor] 监控系统已启动...")
    while True:
        print("👁️ [Monitor] 正在检测系统状态 (嘟...嘟...)")
        time.sleep(1)


def api_rookie_mistake() -> None:
    """
    【案发现场/初级代码】
    新手经典死法 1：把 target 写成了 target=worker_task()，导致直接在主线程串行执行，根本没开新线程。
    新手经典死法 2：开启了无限循环的 monitor_task 但没设置 daemon，导致主程序永远无法退出，变成僵尸进程。
    """
    pass


def pythonic_api_engine() -> Dict[str, bool]:
    """
    TODO: 在此使用指定的 Python API 完成高阶实战

    实战要求：
    1. 创建一个普通线程执行 `worker_task`，任务名为 "Data_Sync"，耗时 3 秒。
    2. 创建一个监控线程执行 `monitor_task`，要求：它必须随着主程序的退出而自动销毁。
    3. 正确启动这两个线程。
    4. 主线程必须等待 `worker_task` 彻底执行完毕。
    5. 返回一个字典，记录主线程结束前，这两个线程的最终存活状态 (用 thread.is_alive() 获取)。
    """
    # TODO 1: 实例化 worker 线程对象
    worker = threading.Thread(target=worker_task, args=("Data_Sync", 3))

    # TODO 2: 实例化 monitor 线程对象 (注意它的属性设置)
    monitor = threading.Thread(target=monitor_task, daemon=True)
    # TODO 3: 启动它们
    worker.start()
    monitor.start()
    # TODO 4: 阻塞主线程，等待 worker 线程完成
    worker.join()
    # TODO 5: 收集状态
    status_report = {
        "worker_alive": worker.is_alive(),  # 替换为真实 API 调用
        "monitor_alive": monitor.is_alive(),  # 替换为真实 API 调用
    }

    print("🏁 主线程核心逻辑执行完毕，准备退出。")
    return status_report


# ================= 3. 黑盒测试 (Test Cases：API 严苛审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行 API 级黑盒测试 ---")
    start_time: float = time.time()

    try:
        status = pythonic_api_engine()
    except Exception as e:
        raise AssertionError(f"❌ API 调用直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 审判 1：主线程是否真的等了 worker_task？
    if total_cost < 3.0:
        raise AssertionError(
            "❌ API 调用失效：你没有使用 join() 阻塞主线程，或者 target 传参错误，导致主线程提前跑路了！"
        )

    # 审判 2：worker 是否已经死亡？
    if status["worker_alive"]:
        raise AssertionError(
            "❌ 生命周期错误：主线程结束时，worker 线程居然还在运行？你到底 join 了没有？"
        )

    # 审判 3：monitor 是否还活着（被 daemon 机制接管前）？
    if not status["monitor_alive"]:
        raise AssertionError(
            "❌ 守护配置错误：monitor_task 是死循环，此时它应该还活着，只是会在几毫秒后随主线程一起被系统超度。"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你精准控制了线程的生与死。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：API 降维打击) =================
"""
🧠 慢思考拷问 (源码级教官的灵魂一问)：
针对你刚刚完成的【节点 1 & 2】，回答以下两个直击底层的问题：

1. 守护线程的“暴毙”隐患：
   当 `daemon=True` 的线程随主线程退出而瞬间死亡时，它是被操作系统“温柔地通知退出”，还是“直接拔电源物理斩首”？如果你的 `monitor_task` 里正好打开了一个文件在写日志（`with open(...)`），此时主线程结束，会发生什么灾难？

2. GIL 的幽灵 (Node 1 核心考核)：
   假设我把 `worker_task` 里面的 `time.sleep(3)` 换成了一个死循环计算 `while True: 1 + 1`，并且我同时开启了 4 个这样的 Worker 线程。
   在你的 8 核电脑上，你打开任务管理器，CPU 的整体利用率大概会是多少？这 4 个线程是真的在 4 个不同的 CPU 核心上“并行”计算吗？为什么？

👉 回答区：1、是被操作系统“温柔地通知退出”，没有内存泄漏的灾难，因为daemon=True是温柔退出的。
2、CPU 的整体利用率大概1/8，不在不同的CPU核心，因为线程是执行调度的最小的单元，它没得资源，它是包含在一个进程里面的。
"""
