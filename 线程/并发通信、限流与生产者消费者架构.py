# ================= 0. 知识点与 API 映射 (快思考) =================
"""
【节点 4 & 6 融合：通信原语与生产消费模型 (Coordination & Producer-Consumer)】

🧠 直觉模型与架构映射：
在复杂的并发系统中，线程不能只顾自己跑，它们需要“听指挥”和“传数据”。

1. Event (全局广播/发令枪)：
   - 直觉：一个跨线程的红绿灯。
   - 场景：系统初始化未完成前，所有工作线程必须挂起等待；一旦主线程完成自检，按下绿灯，所有线程瞬间同时启动。

2. Semaphore (并发限流器)：
   - 直觉：夜店门口的保安，手里只有 3 张通行证。即使外面有 100 个人排队，里面最多只能进 3 个人。
   - 场景：限制同时访问某个脆弱 API（如数据库连接池、外部大模型接口）的最大线程数。

3. queue.Queue (安全传送带)：
   - 直觉：一条带缓冲区的流水线传送带。生产者只管往上放零件，消费者只管从另一头取。
   - 场景：解耦数据的“生产速率”和“消费速率”。完美解决数据共享时的竞态条件（Queue 内部已经用锁封装好了）。

🛠️ 核心 API 兵器谱 (参数级精讲)：

- threading.Event:
  - `event.set()`: 变绿灯（内部 Flag 设为 True），唤醒所有正在等待的线程。
  - `event.clear()`: 变红灯（内部 Flag 设为 False）。
  - `event.wait(timeout)`: 阻塞当前线程，直到灯变绿。如果超时返回 False。

- threading.Semaphore:
  - `sema = threading.Semaphore(value)`: 初始化保安手里的通行证数量。
  - `sema.acquire()`: 拿走一张通行证。如果没有了，就阻塞等待。
  - `sema.release()`: 还回一张通行证，唤醒一个等待的人。

- queue.Queue:
  - `q = queue.Queue(maxsize)`: 创建队列，maxsize 限制传送带长度（防内存 OOM）。
  - `q.put(item, block=True, timeout)`: 往队列放数据。如果满了且 block=True，就阻塞等。
  - `q.get(block=True, timeout)`: 从队列取数据。如果空了，就阻塞等。
  - `q.task_done()`: 【重点】消费者每次处理完一个从 get() 拿到的任务，必须调一次这个。
  - `q.join()`: 【终极阻塞】主线程调用，阻塞直到队列里所有的任务都被 `task_done()` 标记为完成。
"""

# ================= 1. 依赖导入 (Imports) =================
import threading
import queue
import time
from typing import List

# ================= 2. API 实战场 (API Battleground) =================


def api_rookie_mistake() -> None:
    """
    【案发现场/初级代码】
    新手死法 1：用 list.append() 和 while 轮询来做生产者消费者，导致 CPU 占用率 100%，且丢失数据。
    新手死法 2：主线程调了 `queue.join()` 死等，但消费者线程里忘了写 `queue.task_done()`，导致主线程永久死锁卡死。
    """
    pass


class VisionPipeline:
    """
    实战场景：这是一个视觉帧处理管线。
    - 摄像头（生产者）不断采集图像帧。
    - 推理引擎（消费者）不断获取图像帧进行分析。
    - 系统受限于硬件算力，必须严格控制最大并发推理数量。
    - 必须有全局启停控制机制。
    """

    def __init__(self, max_concurrent_inference: int):
        self.frame_queue = queue.Queue(maxsize=10)
        self.processed_count = 0

        # TODO 1: 初始化一个事件对象，作为系统的“运行总开关”
        self.system_running = threading.Event()

        # TODO 2: 初始化一个信号量对象，用于限制最大的并发推理数
        self.inference_sema = threading.Semaphore(max_concurrent_inference)

        # 用于安全计数
        self.count_lock = threading.Lock()

    def camera_sensor(self, total_frames: int) -> None:
        """生产者：生成图像帧放入队列"""
        # TODO 3: 等待系统总开关开启后，才开始生产
        self.system_running.wait()

        for i in range(total_frames):
            frame_id = f"Frame_{i}"
            # TODO 4: 将 frame_id 放入队列 (需考虑如果系统开关关闭，应如何提前退出)
            self.frame_queue.put(frame_id)
        print("生产者运行完毕")

    def inference_engine(self) -> None:
        """消费者：从队列获取帧并处理"""
        while True:
            # TODO 5: 优雅地从队列获取任务。如果系统已经发出了停止信号且队列为空，应退出循环结束线程。
            if not self.system_running.is_set() and self.frame_queue.empty():
                break

            try:
                result = self.frame_queue.get(timeout=0.05)
            except queue.Empty as e:
                print(f"发生了错误:{e}")
                continue

            # TODO 6: 使用信号量限制此处的并发处理量，并模拟耗时 0.1 秒的处理过程。
            # 处理完成后，务必安全地更新 self.processed_count。
            try:
                with self.inference_sema:
                    time.sleep(0.1)
                    with self.count_lock:
                        self.processed_count += 1
            finally:
                # TODO 7: 发送队列任务完成信号
                self.frame_queue.task_done()


def pythonic_api_engine(total_frames: int, max_concurrent: int) -> int:
    """
    TODO 8: 编写引擎驱动逻辑。
    1. 实例化 VisionPipeline。
    2. 开启 1 个 camera_sensor 线程。
    3. 开启 5 个 inference_engine 线程。
    4. 启动所有线程后，开启“系统总开关”。
    5. 等待所有帧被彻底处理完毕。
    6. 关闭系统，确保所有线程安全退出。
    7. 返回最终处理的帧数量。
    """

    vis = VisionPipeline(max_concurrent)

    camera_thread = threading.Thread(
        target=vis.camera_sensor,
        args=(total_frames,),
    )

    worker_threads = [threading.Thread(target=vis.inference_engine) for _ in range(5)]

    camera_thread.start()

    for thread in worker_threads:
        thread.start()

    vis.system_running.set()

    camera_thread.join()

    vis.frame_queue.join()

    vis.system_running.clear()

    for thread in worker_threads:
        thread.join()

    return vis.processed_count


# ================= 3. 黑盒测试 (Test Cases：API 严苛审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行 API 级黑盒测试 ---")
    start_time: float = time.time()

    TOTAL_FRAMES = 20
    MAX_CONCURRENT = 2

    try:
        final_count = pythonic_api_engine(TOTAL_FRAMES, MAX_CONCURRENT)

        if final_count != TOTAL_FRAMES:
            raise AssertionError(
                f"❌ 数据丢失！期望处理 {TOTAL_FRAMES} 帧，实际处理了 {final_count} 帧。"
            )

    except Exception as e:
        raise AssertionError(f"❌ 熔炉爆炸 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 算力压测验证：
    # 20 帧，每次耗时 0.1s。如果不限制并发，5 个消费者最快需 0.4s。
    # 但信号量限制了最大并发为 2，所以理论最快时间 = (20 / 2) * 0.1 = 1.0s。
    # 加上调度开销，时间应在 1.0s 到 1.3s 之间。
    if total_cost < 0.9:
        raise AssertionError(
            f"❌ 信号量失效！总耗时 {total_cost:.2f}s 过短，你没有成功限制最大并发数！"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功构建了工业级的多线程通信管线！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：API 降维打击) =================
"""
🧠 慢思考拷问 (源码级教官的灵魂一问)：

1. `queue.Queue` 之所以被称为“线程安全的完美封装”，是因为它的底层 CPython 源码中使用了我们节点 4 提到的 `Condition`（条件变量）。
请结合你对 `queue` API 的理解，推演一下：当队列为空时，消费者调用 `q.get()` 发生了什么？它是如何做到“不消耗 CPU 资源地死等”，并且在生产者调用 `q.put()` 时瞬间被唤醒的？

2. 致命细节：如果你的代码里，消费者虽然调用了 `q.get()` 拿到了数据，但如果后续逻辑发生异常崩溃了，没有执行到 `q.task_done()`，这对主线程调用的 `q.join()` 会产生什么毁灭性的打击？为什么 API 要这么设计，而不是直接用 `get()` 的次数来判断任务是否完成？

👉 回答区：q.get()队列里面的数据被取出来啊。锁的机制吗？
2、直接卡死了，因为统计的次数不是原子的。
"""
