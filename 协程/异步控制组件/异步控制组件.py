"""
【业务场景】 (Context)
你正在开发一个针对大语言模型 (LLM) 的批量数据清洗脚本。
你有 1000 条长文本需要发送给 OpenAI 或商汤的 API 进行信息抽取。
痛点在于：上游 API 极其严格，你的账号限制了“最大并发数不能超过 10”。如果超过 10 个并发请求同时到达，上游会直接封禁你的 IP 或返回 HTTP 429 (Too Many Requests)。

【接口契约】 (Contract)
- 输入：`prompts` (一个包含 100 个字符串的列表), `max_concurrent` (允许的最大并发数，例如 10)。
- 输出：返回一个包含 100 个处理结果的列表，且结果顺序必须与输入顺序完全一致。
- 约束/异常：
  1. 在任何物理时刻，正在执行 `call_remote_llm_api` 的并发数量绝对不能超过 `max_concurrent`。
  2. 必须处理并返回所有结果。
- 工程提示：思考在批量创建协程任务时，如何将 `asyncio.Semaphore` 优雅地绑定到每一个独立的网络请求上？
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import asyncio
from typing import List

# ================= 2. 代码骨架 (Starter Code) =================

# --- 模拟上游服务端（严禁修改） ---
_active_connections = 0
_max_observed_connections = 0


async def call_remote_llm_api(prompt: str) -> str:
    """
    【危险地带】模拟上游脆弱的 API 接口，内置并发检测器。
    注意：在真实测试中，绝对不要修改这个函数！
    """
    global _active_connections, _max_observed_connections

    _active_connections += 1
    # 记录历史最高并发数
    if _active_connections > _max_observed_connections:
        _max_observed_connections = _active_connections

    # 模拟网络延迟和推理时间 (50ms - 150ms 不等)
    await asyncio.sleep(0.1)

    _active_connections -= 1
    return f"PROCESSED_[{prompt}]"


# ----------------------------------


async def target_function(prompts: List[str], max_concurrent: int) -> List[str]:
    async def _sem_func(prompt: str, sem):
        async with sem:
            result = await call_remote_llm_api(prompt)
            return result

    sem = asyncio.Semaphore(max_concurrent)
    work = [_sem_func(prompt, sem) for prompt in prompts]
    task_result = await asyncio.gather(*work)
    return task_result


# ================= 3. 黑盒测试 (Test Cases) =================
async def _async_test_runner():
    global _active_connections, _max_observed_connections
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    _active_connections = 0
    _max_observed_connections = 0

    # 生成 100 条测试数据
    test_prompts = [f"Data_{i}" for i in range(100)]
    limit = 10

    start_time = time.time()
    results = await target_function(test_prompts, limit)
    total_time = time.time() - start_time

    # 测试 1：基础核心链路 (Happy Path)
    assert len(results) == 100, f"结果数量不对！预期 100，实际 {len(results)}"
    assert (
        results[0] == "PROCESSED_[Data_0]"
    ), "数据处理逻辑或顺序错误，你是否打乱了输入输出的对应关系？"
    assert results[99] == "PROCESSED_[Data_99]", "尾部数据处理错误"

    # 测试 2：流量阀门拦截校验 (Rate Limit Engine)
    print(
        f"📊 监控指标：允许的最大并发 = {limit}，实际探测到的峰值并发 = {_max_observed_connections}"
    )

    if _max_observed_connections > limit:
        raise AssertionError(
            f"❌ 灾难级 Bug：你把上游 API 打挂了！峰值并发达到了 {_max_observed_connections}，远超限制的 {limit}。"
        )
    elif _max_observed_connections < limit:
        print(
            "⚠️ 警告：你的并发峰值没有达到上限，系统可能过于保守，未充分榨取带宽。但算作通过。"
        )

    # 测试 3：死锁与耗时校验
    # 100 个任务，每次并发 10 个，每批大约耗时 0.1 秒，总耗时应该在 1.0 秒出头。
    if total_time > 2.0:
        raise AssertionError(
            "⚠️ 性能严重不达标：耗时过长，你是否不小心把异步写成了串行 (for 循环里直接 await)？"
        )

    print(f"⏱️ 100条数据处理总耗时: {total_time:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功构建了一个工业级流量整形器。")


def test_crucible():
    asyncio.run(_async_test_runner())


if __name__ == "__main__":
    test_crucible()
