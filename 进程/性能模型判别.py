# ================= 0. 知识点讲解 =================
"""
【性能模型判别 (CPU 密集型 vs I/O 密集型)】

直觉模型：
不要手里拿着多进程的锤子，看什么都是钉子！
在 Python 中，因为存在臭名昭著的 GIL（全局解释器锁），多线程在同一时刻只能执行一行 Python 字节码。
但这并不意味着多线程没用。操作系统的底层逻辑决定了我们需要“兵分两路”：

1. CPU 密集型 (CPU-Bound)：疯狂消耗 CPU 算力（如：加密解密、图像渲染、千万级循环计算）。
   - 痛点：需要真正的多核并行。
   - 武器库：必须用 `多进程 (ProcessPoolExecutor)`。如果用多线程，多个线程抢一把 GIL 锁，反而比单线程还慢！

2. I/O 密集型 (I/O-Bound)：疯狂等待外部响应（如：网络爬虫、读写磁盘、请求数据库）。
   - 痛点：CPU 闲得发慌，都在死等网络。而在等待期间，Python 会**自动释放 GIL 锁**！
   - 武器库：必须用 `多线程 (ThreadPoolExecutor)` 或 `协程 (Asyncio)`。如果用多进程，进程创建的巨大内存开销和切换成本纯属浪费，且进程池数量有限，排队会急死人。
"""

# ================= 1. 依赖导入 (Imports) =================
import concurrent.futures
import time

# ================= 2. 代码骨架 (Starter Code) =================


def heavy_cpu_task(task_id):
    """【模拟 CPU 密集型】疯狂的循环计算。占用大量 CPU 时间。"""
    count = 0
    # 这个循环在普通机器上大概需要 0.3 ~ 0.5 秒
    for i in range(10**7):
        count += 1
    return f"CPU任务-{task_id} 完成"


def heavy_io_task(task_id):
    """【模拟 I/O 密集型】网络请求/数据库查询。CPU 完全空闲，只是在死等响应。"""
    time.sleep(0.5)  # 模拟等待网络响应 0.5 秒
    return f"IO任务-{task_id} 完成"


def smart_architect_engine(cpu_task_count, io_task_count):
    """
    TODO: 在此实现你的智能分发引擎
    要求：
    1. 你面对的是混合任务。请根据任务的物理特性，将它们分配给最合适的“池”。
    2. 创建一个 max_workers=4 的 ProcessPoolExecutor 处理 CPU 任务。
    3. 创建一个 max_workers=10 的 ThreadPoolExecutor 处理 I/O 任务。
    4. 将两种凭证 (Future) 合并收割，统一返回 results 列表。
    """
    results = []

    # TODO 1: 同时启动两支不同的包身工团队（进程池 & 线程池）
    with concurrent.futures.ProcessPoolExecutor(
        cpu_task_count
    ) as p_pool, concurrent.futures.ThreadPoolExecutor(io_task_count) as t_pool:
        # TODO 2: 派发 CPU 任务给合适的池
        cpu_futures = [p_pool.submit(heavy_cpu_task, i) for i in range(cpu_task_count)]

        # TODO 3: 派发 I/O 任务给合适的池
        io_futures = [t_pool.submit(heavy_io_task, i) for i in range(io_task_count)]

        # TODO 4: 统一收割结果
        all_futures = cpu_futures + io_futures
        for f in concurrent.futures.as_completed(all_futures):
            results.append(f.result())

    return results


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()

    # 派发 4 个 CPU 任务，10 个 IO 任务
    results = smart_architect_engine(cpu_task_count=4, io_task_count=10)

    cost = time.time() - start_time

    if len(results) != 14:
        raise AssertionError("❌ 灾难级 Bug：任务丢失了！")

    print(f"⏱️ 智能引擎总耗时: {cost:.4f} 秒")

    # 【核心架构验证逻辑】
    # 如果完全分配正确：
    # CPU任务(4个)在4核进程池里真并行，约耗时 0.4s。
    # IO任务(10个)在10个线程池里并发等待，约耗时 0.5s。
    # 两者同时进行，总耗时应该是 max(0.4, 0.5) ≈ 0.5 ~ 0.8 秒左右。

    # 💥 如果乱分配：
    # 若全放线程池：CPU任务受GIL限制变为串行，单CPU耗时 4 * 0.4 = 1.6秒以上。
    # 若全放进程池：只有4个进程，10个IO任务需要排队，至少 3 轮，耗时 3 * 0.5 = 1.5秒以上。

    if cost > 1.2:
        raise AssertionError(
            "❌ 架构严重失误：耗时过长！\n"
            "如果你超过了 1.2 秒，说明你遭遇了排队等待或 GIL 锁死。\n"
            "检查：是不是把 I/O 任务扔进进程池了？或者把 CPU 任务扔进线程池了？"
        )

    print(
        "✅ All Tests Passed! 恭喜 AC！你拥有了首席架构师的性能嗅觉，完美驾驭了混合计算模型。"
    )


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
假设你用 `asyncio` (协程) 写了一个极其高效的网络爬虫，每秒可以并发下载 100 张图片 (绝对的 I/O 密集型)。
然后你的产品经理要求：图片下载完后，立刻在代码里用 `OpenCV` (一个纯 CPU 密集型的图像处理库) 给图片加个滤镜，然后再保存。

请在脑海中推演：如果你直接在异步函数 (`async def`) 里调用 `OpenCV` 去算矩阵加滤镜，你那原本极度高效的爬虫会发生什么可怕的事情？
为了保住爬虫的高并发能力，你应该怎么处理这个 OpenCV 滤镜任务？（提示：结合今天学到的知识）
回答：对于cv任务这个是CPU密集型任务，应该使用多进程，这个应该是一个同步函数，得将这个同步函数放在进程池里面，在协程里面处理的方法应该是这样的。
"""
