# ================= 0. 知识点讲解 (终局复盘) =================
"""
【终局实战：异构数据处理引擎 (Nexus Core)】

直觉模型：
真实的机器人视觉或大数据 ETL 场景中，从来都不是单一的。
1. 传感器/网络抓包：纯 I/O 密集型，数据源源不断。我们用轻量级的【线程】去扛。
2. 图像矩阵/张量计算：纯 CPU 密集型，算力要求极高。我们用重量级的【多进程】去扛。
3. 它们之间通过多进程安全的【Queue】进行跨边界数据传输 (IPC)。
4. 为了防止僵尸进程，我们使用全局的【Event】作为红绿灯，实现“优雅停机 (Graceful Shutdown)”。
5. 所有节点都在独立的内存空间狂奔，必须用【QueueListener】进行中心化日志收集。
6. 最底层的防线：绝对不能忘了平台兼容性 (spawn)。
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import threading
import logging
import logging.handlers
import time
import os
import queue  # 用于捕获 queue.Empty 异常

# ================= 2. 代码骨架 (Starter Code) =================


def cpu_vision_worker(worker_id, data_queue, log_queue, stop_event):
    """
    【CPU 密集型子进程】
    从队列获取传感器数据进行计算。必须安全处理日志发报和优雅停机。
    """
    # TODO 1: 配置子进程的专属 Logger 与发报机 (战区五防线)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []
    qh = logging.handlers.QueueHandler(log_queue)
    root_logger.addHandler(qh)

    logging.info(f"视觉算力核心-{worker_id} 已上线，等待数据...")

    # TODO 2: 实现【优雅停机】的防死锁死循环 (战区一、战区二防线)
    # 要求：只要 stop_event 没有被拉响，就继续干活。
    # 警告：data_queue.get() 默认是死等！如果主程序发了停机信号但队列没数据了，进程会永久死锁卡死在这里。
    # 提示：必须设置 timeout，并捕获 queue.Empty 异常，在异常里用 continue 继续下一轮的 while 检查。

    while True:
        try:
            data = data_queue.get(timeout=0.5)
            # 模拟极度消耗 CPU 的视觉矩阵处理
            time.sleep(0.3)
            logging.info(f"视觉算力核心-{worker_id} 成功处理: {data}")
        except queue.Empty:
            if stop_event.is_set():
                break
            else:
                continue

    logging.info(f"视觉算力核心-{worker_id} 收到停机指令，安全撤离！")


def io_sensor_thread(data_queue, stop_event):
    """
    【I/O 密集型线程】
    模拟从网络/串口高频读取传感器数据，塞入队列。
    """
    logging.info("传感器 I/O 线程启动，开始采集数据...")
    for i in range(5):
        time.sleep(0.1)  # 模拟 I/O 阻塞耗时
        data = f"Frame-{i}"
        data_queue.put(data)
        logging.info(f"采集线程抓取新数据并推入流水线: {data}")

    logging.info("传感器数据流结束，准备发送全局停机信号！")

    # TODO 3: 触发全局发令枪，通知所有正在死循环里的 CPU 进程下班 (战区二防线)
    stop_event.set()


def nexus_core_engine():
    """
    TODO: 在此实现主架构调度引擎
    """
    # TODO 4: 封死操作系统的克隆地雷，设置启动模式为 'spawn' (战区四防线)
    multiprocessing.set_start_method("spawn", force=True)

    # 1. 建立 IPC 队列与全局发令枪
    data_queue = multiprocessing.Queue()
    log_queue = multiprocessing.Queue()
    stop_event = multiprocessing.Event()

    # 2. 建立中心化日志塔
    log_filename = "nexus_engine.log"
    if os.path.exists(log_filename):
        os.remove(log_filename)
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")

    # TODO 5: 配置标准 Formatter，并启动 QueueListener (战区五防线)
    # 格式要求：[%(asctime)s] - [%(process)d] - [%(levelname)s] - %(message)s
    # 注意避开上一关的时间穿透陷阱！
    fmt = "[%(asctime)s] - [%(process)d] - [%(levelname)s] - %(message)s"
    formatter = logging.Formatter(fmt)
    file_handler.setFormatter(formatter)
    listener = logging.handlers.QueueListener(log_queue, file_handler)
    listener.start()

    # 3. 启动混编包身工团队 (1个 采集线程 + 2个 算力进程)
    print("[引擎] 正在启动 I/O 线程与 CPU 进程池...")

    cpu_processes = []
    for i in range(2):
        p = multiprocessing.Process(
            target=cpu_vision_worker, args=(i, data_queue, log_queue, stop_event)
        )
        p.start()
        cpu_processes.append(p)

    sensor_t = threading.Thread(target=io_sensor_thread, args=(data_queue, stop_event))
    sensor_t.start()

    # 4. 等待所有任务彻底结束
    sensor_t.join()
    for p in cpu_processes:
        p.join()

    # TODO 6: 所有的兵都打完仗了，完美停机，通知通讯兵收尾并下班。
    listener.stop()

    print("[引擎] 所有节点已优雅关闭。系统停机。")
    return log_filename


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行终局黑盒测试 ---")

    start_time = time.time()
    log_file = nexus_core_engine()
    total_cost = time.time() - start_time

    if not os.path.exists(log_file):
        raise AssertionError("❌ 灾难级 Bug：中心化日志文件未生成！")

    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()

    # 核心架构验证 1：有没有僵尸进程？
    if "安全撤离" not in log_content:
        raise AssertionError(
            "❌ 优雅停机失败：CPU 进程没有正常退出，大概率死锁在 data_queue.get() 上了！"
        )

    # 核心架构验证 2：混合并发的性能榨取
    # 5个数据产生共耗时 0.5s，2个进程处理5个数据(每个0.3s)约耗时 0.9s。
    # 异步流水线同时工作，总时间应该在 1.0s ~ 1.5s 之间。如果退化为串行，耗时会超过 2s。
    print(f"⏱️ 引擎运行总耗时: {total_cost:.4f} 秒")
    if total_cost > 2.0:
        raise AssertionError(
            "❌ 并发失效：耗时过长，你的 I/O 线程和 CPU 进程之间发生了严重的阻塞等待！"
        )

    # 核心架构验证 3：日志中心化验证
    if "Frame-4" not in log_content:
        raise AssertionError("❌ 数据丢失：不是所有的 Frame 都被处理并记录了！")

    print("\n" + "=" * 40)
    print("🏆 恭喜通关！你已征服 Python 工业级多进程并发架构！")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在 TODO 2 中，我们通过 `Event` 和 `get(timeout=1)` 实现了优雅停机。
但在真实的 Linux 服务器上，如果系统内存突然爆满，OOM Killer (Out Of Memory 杀手) 可能会直接发出 `SIGKILL (kill -9)` 信号，瞬间极其野蛮地秒杀掉你其中一个 `cpu_vision_worker` 进程。

一旦发生这种硬杀，子进程甚至连 `finally` 代码块都来不及执行就死了。
请在脑海中推演：如果这个子进程死亡的那一瞬间，它刚好正在对 `data_queue` 执行底层加锁的提取动作，那么**主进程和其他子进程**接下来会发生什么极其可怕的灾难？
在像 Celery 或 Hadoop 这样的顶级工业界分布式系统中，架构师通常会引入什么机制，来防范这种“底层锁损坏导致的全局死锁”？

回答：死锁了，架构师会使用with，也就是使用了__exit__。
"""
