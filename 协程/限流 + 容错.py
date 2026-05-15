"""
【业务场景】 (Context)
在机器人底层控制系统中，主控节点需要并发读取 50 个伺服电机（Joint）的当前温度和状态。
痛点一：总线的带宽有限，最大允许的并发读取数不能超过 5（需要复习 Semaphore）。
痛点二：硬件总是不稳定的。某几个伺服电机可能因为掉线或过热，读取时会直接抛出 `TimeoutError`。
如果在并发读取时，因为一个电机的报错导致整个测温脚本崩溃，机器人就会彻底失去状态监控。

【接口契约】 (Contract)
- 输入：`joint_ids` (包含 50 个电机 ID 的列表), `max_concurrent` (最大并发数 5)。
- 输出：返回一个包含 50 个状态的列表。
- 约束/异常：
  1. 必须限制并发数（复习上一关）。
  2. 【新增要求】如果某个电机读取抛出了异常（如 TimeoutError），网关绝不能崩溃。该电机在返回列表中的结果应显示为 `"OFFLINE"`。
  3. 最终返回的 50 个状态顺序，必须和输入的 `joint_ids` 顺序一一对应。
- 工程提示：思考在 `_sem_func` 内部，或者在 `asyncio.gather` 的参数中，应该如何拦截和转化异常？
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import asyncio
from typing import List

# ================= 2. 代码骨架 (Starter Code) =================


# --- 模拟底层硬件总线（严禁修改） ---
async def read_joint_state(joint_id: int) -> str:
    """
    【危险地带】模拟硬件读取。部分特定的 ID 会固定触发异常。
    """
    # 模拟网络/总线延迟
    await asyncio.sleep(0.05)

    # 模拟硬件故障：4 号和 17 号电机掉线，直接抛出异常
    if joint_id in (4, 17):
        raise TimeoutError(f"Joint_{joint_id} is not responding!")

    return f"OK_TEMP_3{joint_id}C"


# ----------------------------------


async def target_function(joint_ids: List[int], max_concurrent: int) -> List[str]:
    async def _sem_func(joint_id: str, sem):
        async with sem:
            result = await read_joint_state(joint_id)
            return result

    sem = asyncio.Semaphore(max_concurrent)
    work = [_sem_func(joint_id, sem) for joint_id in joint_ids]
    task_result = await asyncio.gather(*work, return_exceptions=True)
    for i in range(len(task_result)):
        if isinstance(task_result[i], TimeoutError):
            task_result[i] = "OFFLINE"
    return task_result


# ================= 3. 黑盒测试 (Test Cases) =================
async def _async_test_runner():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    test_ids = list(range(20))  # 测试 0 到 19 号电机
    limit = 5

    start_time = time.time()
    try:
        results = await target_function(test_ids, limit)
    except Exception as e:
        raise AssertionError(
            f"❌ 灾难级 Bug：异常穿透了！主协程被异常 {type(e).__name__} 击穿。"
        )

    total_time = time.time() - start_time

    # 测试 1：基础核心链路与顺序 (Happy Path)
    assert len(results) == 20, "结果数量不对！"
    assert results[0] == "OK_TEMP_30C", "正常数据处理错误"
    assert results[19] == "OK_TEMP_319C", "正常数据处理错误"

    # 测试 2：容错与降级拦截校验 (Fault Tolerance Engine)
    assert (
        results[4] == "OFFLINE"
    ), "❌ 容错失败：4号电机应该返回 'OFFLINE'，你是否正确捕获了异常？"
    assert results[17] == "OFFLINE", "❌ 容错失败：17号电机应该返回 'OFFLINE'"

    print(f"⏱️ 20个电机读取总耗时: {total_time:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功构建了一个高鲁棒性的硬件状态采集器。")


def test_crucible():
    asyncio.run(_async_test_runner())


if __name__ == "__main__":
    test_crucible()
