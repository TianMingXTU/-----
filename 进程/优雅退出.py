# ================= 0. 知识点讲解 =================
"""
【工程核心之“优雅退出” (Graceful Shutdown)】

直觉模型：
想象一个车间，有 M 个流水线机器（生产者）往唯一的传送带（Queue）上扔零件，有 N 个质检员（消费者）在尽头拿零件。
现在下班铃响了。你不能直接拉电闸（terminate），因为传送带上还有没质检完的零件，而且有些质检员正拿着零件在检查。

正确的下班协议（Poison Pill / Sentinel 机制扩展）：
1. 生产者先停：必须等所有的 M 个机器都把手头的零件做完，停止运转（让 producers 全部 join）。
2. 投放精准数量的下班牌：机器停了，主进程要在传送带上放“下班牌”（通常是 None）。
   - ⚠️ 核心陷阱：放几个？因为每个质检员拿到一个“下班牌”就会自己下班，如果质检员有 N 个，你必须放且仅放 N 个下班牌！
3. 消费者清空与撤退：质检员继续拿零件，直到他们每个人都拿到一个属于自己的“下班牌”，然后安全退出（让 consumers 全部 join）。

为什么要这样？
- 保证数据零丢失：机器做完的零件绝对会被质检员处理完，因为“下班牌”是严格排在所有正常零件后面的。
- 保证不假死：投放了精确数量的“下班牌”，没有任何一个质检员会在空传送带前傻傻死等。
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time
import queue


# ================= 2. 代码骨架 (Starter Code) =================
def producer_worker(p_id, q, items_to_produce):
    """
    生产者：生成指定数量的零件。
    （注：为了保持职责单一，在这个模型中，生产者不下发 None，只管埋头生产）
    """
    for i in range(items_to_produce):
        time.sleep(0.01)  # 模拟生产耗时
        q.put(f"零件-{p_id}-{i}")
    print(f"  [生产者 {p_id}] 生产完毕，正常停机。")


def consumer_worker(c_id, q, counter, lock):
    """消费者：处理零件，直到收到 None"""
    print(f"  [消费者 {c_id}] 准备就绪，开始监听传送带...")
    while True:
        try:
            # 防御性编程：即使是优雅退出，加上 timeout 也是防止由于主进程意外导致的永久死锁的好习惯
            item = q.get(timeout=3)
        except queue.Empty:
            print(f"  [消费者 {c_id}] 异常！等待超时，强制撤离。")
            break

        # TODO 1: 判断是不是下班牌。如果是，打印一句下班的话，并退出循环
        if item is None:
            print("下班了")
            break

        # 模拟处理零件耗时
        time.sleep(0.02)
        # 安全地将计数器 +1 (你已经在节点 0.5.1 完美掌握了这个操作)
        with lock:
            counter.value += 1


def graceful_factory(num_producers, num_consumers, items_per_producer):
    """
    TODO: 实现车间的优雅退出调度逻辑
    """
    q = multiprocessing.Queue()
    counter = multiprocessing.Value("i", 0)
    lock = multiprocessing.Lock()

    producers = []
    consumers = []

    # 1. 启动生产者
    for i in range(num_producers):
        p = multiprocessing.Process(
            target=producer_worker, args=(i, q, items_per_producer)
        )
        p.start()
        producers.append(p)

    # 2. 启动消费者
    for i in range(num_consumers):
        c = multiprocessing.Process(target=consumer_worker, args=(i, q, counter, lock))
        c.start()
        consumers.append(c)

    # TODO 2: 完美停机协议第一步：阻塞主进程，等待所有【生产者】完成工作
    for p in producers:
        p.join()

    # TODO 3: 完美停机协议第二步：根据【消费者】的数量，往 Queue 中投放精确数量的下班牌 (None)
    for j in range(len(consumers)):
        q.put(None)
    # TODO 4: 完美停机协议第三步：阻塞主进程，等待所有【消费者】安全下班
    for c in consumers:
        c.join()
    return counter.value


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")
    start_time = time.time()

    # 场景：3 个生产者，每个生产 10 个零件；5 个消费者去处理。
    # 预期结果：总计 30 个零件被处理完，没有任何进程假死。
    total_processed = graceful_factory(
        num_producers=3, num_consumers=5, items_per_producer=10
    )
    cost_time = time.time() - start_time

    print(f"⏱️ 引擎总停机耗时: {cost_time:.4f} 秒")

    # 测试 1: 数据完整性 (Data Integrity)
    if total_processed != 30:
        raise AssertionError(
            f"❌ 灾难级 Bug：数据丢失或重复！期望处理 30 个，实际计数器为 {total_processed} 个。"
        )

    # 如果你的程序能运行到这里没有卡死，说明 join 逻辑和 None 的数量发对了！
    print("✅ All Tests Passed! 恭喜 AC！你掌握了多进程最优雅的落幕。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
请你在脑海中推演一个极其常见的初学者错误：
如果我在 TODO 2 和 TODO 3 的顺序弄反了——也就是主进程【还没等生产者结束】，就直接往 Queue 里扔了 N 个 None，
系统会发生什么可怕的数据灾难？（提示：想想传送带上的零件顺序，以及消费者的反应）。
回答：也就是说业务数据会丢失，因为现在的队列是数据、停止、数据。
"""
