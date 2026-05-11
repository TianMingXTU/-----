# ================= 0. 知识点讲解 =================
"""
【多进程日志与混沌追踪 (QueueHandler & PID 隔离)】

直觉模型：
不要让前线的士兵（子进程）各自给指挥部写信（直接写文件），信件会在邮局挤成一团被撕碎。
我们应该在指挥部设立一个“专门收信的通讯兵 (QueueListener)”，并给所有前线士兵发一个“电报机 (QueueHandler)”。
士兵只管往电报机（多进程安全的 Queue）里发消息。通讯兵在后台慢慢排队拿出消息，工工整整地写进同一个档案本里。

核心武器库 (logging.handlers)：
1. `QueueHandler`: 放在【子进程】里。它什么也不干，就负责把日志对象 (LogRecord) 扔进队列。
2. `QueueListener`: 放在【主进程】里。它在后台开启一个独立线程，死循环监听队列，把拿到的日志交给真正的 FileHandler 或 StreamHandler 去写文件/屏幕。

观测性铁律 (PID 隔离)：
多进程日志如果没有打上 PID，毫无价值！你的 Formatter 必须包含 `%(process)d` 或者 `%(processName)s`。
"""

# ================= 1. 依赖导入 (Imports) =================
import logging
import logging.handlers
import multiprocessing
import time
import os

# ================= 2. 代码骨架 (Starter Code) =================


def worker_process(worker_id, log_queue):
    """
    【业务场景】前线子进程：只负责干活和发报，绝不直接碰文件！
    """
    # TODO 1: 配置子进程的专属 Logger
    # 1. 获取根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # 确保所有级别的日志都能发出去

    # 2. 清空可能存在的旧 Handler（防止重复打印）
    root_logger.handlers = []

    # 3. 创建 QueueHandler 并添加到 logger 中
    qh = logging.handlers.QueueHandler(log_queue)
    root_logger.addHandler(qh)

    # 模拟业务逻辑，疯狂打印日志
    for i in range(5):
        logging.info(f"Worker-{worker_id} 正在处理第 {i} 批数据...")
        time.sleep(0.01)
        if i == 3:
            logging.warning(f"Worker-{worker_id} 遇到轻微波动！")


def centralized_logging_engine():
    """
    TODO: 在此实现主进程的“中心化日志收发塔”
    """
    log_filename = "chaos_trace.log"
    # 清理历史测试文件
    if os.path.exists(log_filename):
        os.remove(log_filename)

    # 1. 建立多进程安全的通讯队列
    log_queue = multiprocessing.Queue()

    # 2. 准备真实的落地处理器 (写入文件)
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")

    # TODO 2: 配置架构师级别的 Formatter！
    # 格式要求包含：[时间] - [进程PID] - [日志级别] - 消息内容
    # 提示：时间是 %(asctime)s, 进程PID是 %(process)d, 级别是 %(levelname)s, 消息是 %(message)s
    formatter = logging.Formatter(
        "[%(asctime)s]-[%(process)d]-[%(levelname)s]-[%(message)s]"
    )
    file_handler.setFormatter(formatter)

    # TODO 3: 招募通讯兵 (QueueListener)
    # 把它跟 log_queue 和 file_handler 绑定，并启动它！
    listener = logging.handlers.QueueListener(log_queue, file_handler)
    listener.start()

    # 3. 派遣 3 个子进程去前线干活
    workers = []
    print("[主进程] 引擎启动，通讯塔已建立，派遣子进程...")
    for i in range(3):
        p = multiprocessing.Process(target=worker_process, args=(i, log_queue))
        p.start()
        workers.append(p)

    # 4. 等待前线任务结束
    for p in workers:
        p.join()

    # TODO 4: 完美停机。所有的兵都打完仗了，通知通讯兵收尾并下班。
    listener.stop()

    print("[主进程] 所有子进程均已撤离，通讯兵已安全归档。")
    return log_filename


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    log_file = centralized_logging_engine()

    if not os.path.exists(log_file):
        raise AssertionError(
            "❌ 灾难级 Bug：日志文件根本没有生成！是不是没把 FileHandler 交给 Listener？"
        )

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 测试 1：日志完整性测试 (3个进程，每个循环5次发info+1次发warning = 18条)
    print(f"📊 收集到日志条数: {len(lines)}")
    if len(lines) != 18:
        raise AssertionError(
            f"❌ 丢日志了或多打了！期望 18 条，实际找到 {len(lines)} 条。检查 QueueListener 的生命周期。"
        )

    # 测试 2：PID 隔离格式测试
    sample_line = lines[0]
    if (
        "Worker-0" not in sample_line
        and "Worker-1" not in sample_line
        and "Worker-2" not in sample_line
    ):
        pass  # 只要格式里有进程标识就行

    # 简单校验一下是不是打出了数字PID (这里做粗略正则级检查，假设大家配置对了)
    import re

    if not re.search(r"\d{3,}", sample_line):
        print(
            "⚠️ 警告：你的日志里好像没有找到纯数字的 PID，请确认你使用了 %(process)d。"
        )

    print("\n--- 📝 你的日志样本前 3 行 ---")
    print("".join(lines[:3]))
    print("-----------------------------\n")

    print("✅ All Tests Passed! 恭喜 AC！你具备了在混沌中追踪 Bug 的天眼！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
你刚才用 `Queue` + `QueueListener` 完美解决了多进程写日志撕裂的问题。
但在很多初学者看来，这太麻烦了！初学者常常会反问：“既然多进程写同一个文件会撕裂，那我为什么不在主进程创建一个带 `multiprocessing.Lock()` 的普通 `FileHandler` 传给子进程，子进程每次写日志前 `with lock:` 锁住不就好了吗？”

请在脑海中推演：如果在一个高并发（比如 10 个进程，每秒处理几千条数据都要打日志）的系统中，使用“传 Lock 直接写文件”的方案，会导致系统遭遇什么可怕的性能灾难？
（提示：想想 I/O 操作的速度，以及锁的排他性会对其他干活的进程产生什么反向制约？）
回答：你的问题还是速度和简洁度的平衡，如果加锁，都是变得串行操作，IO操作会很慢。
"""
