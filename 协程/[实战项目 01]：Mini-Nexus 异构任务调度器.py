import asyncio
import time
from typing import Any, AsyncGenerator

# ================= 1. 基础设施 (你的干活环境，禁止修改) =================


# 模拟老旧的 C++ 同步视觉处理库 (耗时、霸占 CPU)
def legacy_vision_process(task_id: int, payload: str) -> str:
    # print(f"⚙️ [C++ Worker] 正在处理任务 {task_id}...")
    time.sleep(0.3)  # 同步阻塞！
    return f"processed_{payload}"


# 模拟不稳定的外部云端 API
async def fetch_cloud_payload(task_id: int) -> str:
    if task_id % 4 == 0:  # 模拟部分任务会永远卡死
        await asyncio.sleep(9999)
    await asyncio.sleep(0.5)
    return f"payload_data_{task_id}"


# 模拟流式任务数据库
class AsyncTaskDB:
    async def __aenter__(self):
        print("🔗 [DB] 任务流数据库已连接...")
        await asyncio.sleep(0.1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("🔒 [DB] 任务流数据库已安全断开连接。")

    async def stream_tasks(self, count: int) -> AsyncGenerator[int, None]:
        for i in range(1, count + 1):
            await asyncio.sleep(0.05)  # 模拟流式生成
            yield i


# ================= 2. 你的实战区 =================


class MiniNexusEngine:
    def __init__(self, max_concurrency: int = 5):
        # TODO: 初始化你需要的同步原语（信号量、事件、锁）
        # 以及你的全局状态看板 self.stats = {"success": 0, "failed": 0}
        self.stats = {"success": 0, "failed": 0}
        self.event = asyncio.Event()
        self.sem = asyncio.Semaphore(max_concurrency)
        self.lock = asyncio.Lock()

    async def _process_single_task(self, task_id: int):
        """
        核心工作流：
        1. 等待系统发车信号。
        2. 获取信号量（限流）。
        3. 尝试拉取云端数据（加 1.0 秒超时控制，超时则记录失败并返回）。
        4. 将耗时的 legacy_vision_process 扔给线程池处理。
        5. 安全地获取锁，更新 self.stats["success"] 或 ["failed"]。
        """
        # TODO: 实现单个任务的完整生命周期
        await self.event.wait()
        async with self.sem:
            try:
                result = await asyncio.wait_for(fetch_cloud_payload(task_id), timeout=1)
                res = await asyncio.to_thread(legacy_vision_process, task_id, result)
                async with self.lock:
                    self.stats["success"] += 1
            except TimeoutError as e:
                async with self.lock:
                    self.stats["failed"] += 1
                # raise e

    async def run(self, total_tasks: int):
        """
        主控流：
        1. 启动一个后台任务，在 0.5 秒后触发“系统发车信号”。
        2. 安全打开 AsyncTaskDB。
        3. 流式读取 total_tasks 个任务，为每个任务创建后台处理协程。
        4. 等待所有任务彻底处理完毕。
        """

        tasks = []

        async def task():
            await asyncio.sleep(0.5)
            self.event.set()

        # TODO: 实现总控逻辑
        start = asyncio.create_task(task())
        tasks.append(start)
        async with AsyncTaskDB() as taskdb:
            async for task_id in taskdb.stream_tasks(total_tasks):
                task_ = asyncio.create_task(self._process_single_task(task_id))
                tasks.append(task_)

            await asyncio.gather(*tasks)


# ================= 3. 验收站 (交差验收) =================
def test_crucible():
    print("🚀 启动 Mini-Nexus 核心引擎压测...")

    engine = MiniNexusEngine(max_concurrency=5)
    start_time = time.time()

    # 投放 12 个任务，其中 ID 为 4, 8, 12 的任务会触发网络死机
    asyncio.run(engine.run(total_tasks=12))

    cost_time = time.time() - start_time

    print("\n📊 最终统计面板:", engine.stats)
    print(f"⏱️ 引擎总耗时: {cost_time:.2f} 秒")

    # 验收断言
    assert engine.stats["success"] == 9, "❌ 成功数量不对！"
    assert engine.stats["failed"] == 3, "❌ 失败数量不对！你的超时防御没有生效？"

    # 时序校验：
    # 0.5s等待发车 + 并发处理(12个任务，并发度5，分3批跑完)。
    # 成功任务耗时 ~0.8s (0.5网络 + 0.3计算)
    # 失败任务耗时 1.0s (超时上限)
    # 因为并发处理，整体时间应该控制在 3.0 秒左右，绝对不能超过 4.5 秒！
    assert (
        2.0 < cost_time < 4.5
    ), "❌ 耗时异常！你肯定卡死了事件循环，或者根本没有实现真正的限流并发！"

    print("✅ 架构师级 QA 验收通过！你的调度器不仅能跑，而且防弹！完美收工。")


if __name__ == "__main__":
    test_crucible()
