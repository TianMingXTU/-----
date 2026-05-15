"""
【业务场景】 (Context)
你正在为 Nexus 任务调度引擎编写单机版的 DAG 执行核心。
系统接收到一个任务流拓扑图，你需要按依赖顺序执行它们。
痛点在于：不仅要保证执行顺序正确，还必须做到“最大化并发”——只要前置依赖已经满足的任务，必须立刻并行执行，绝对不能浪费 CPU 时间。

【接口契约】 (Contract)
- 输入：`dag` (字典，键为任务名称，值为该任务依赖的父任务列表)。例如：{"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}
- 输出：返回一个字典，包含所有任务的执行结果。
- 约束/异常：
  1. 保证有依赖关系的任务按顺序执行。
  2. 保证没有直接依赖关系的任务并发执行。
- 工程提示：
  1. 不要提前去写死执行顺序。
  2. 思考 `asyncio.create_task` 的作用。只要把任务创建为 Task，它就会被事件循环自动调度执行。下游任务只需要 `await` 这些 Task 即可。
  在 asyncio 中，每一个被包装为 Task 的协程，本身就是一个 Future（我们在 Level 2 刚刚学过！）。
  你可以把任务包装成 Task 并存在一个字典里。
  下游任务启动时，只需要去字典里把依赖的 Task 找出来，然后 await 它们即可。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import asyncio
from typing import Dict, List, Any

# ================= 2. 代码骨架 (Starter Code) =================


# --- 模拟耗时的计算节点（严禁修改） ---
async def run_node(node_name: str) -> str:
    """模拟每个节点需要耗时 0.1 秒"""
    print(f"   [执行] 节点 {node_name} 开始运转...")
    await asyncio.sleep(0.1)
    return f"RESULT_{node_name}"


# ----------------------------------


async def execute_dag(dag: Dict[str, List[str]]) -> Dict[str, str]:

    async def _run_single_node(node_name: str, deps: List[str]):
        if deps:
            await asyncio.gather(*[tasks[d] for d in deps])
        result = await run_node(node_name)
        return result

    tasks = {}
    for node, deps in dag.items():
        tasks[node] = asyncio.create_task(_run_single_node(node, deps))

    node = list(dag.keys())

    result = await asyncio.gather(*tasks.values())

    result_dict = dict(zip(node, result))
    return result_dict


# ================= 3. 黑盒测试 (Test Cases) =================
async def _async_test_runner():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    # 定义一个经典的菱形 DAG
    #       A
    #     /   \
    #    B     C
    #     \   /
    #       D
    # 预期执行逻辑：
    # T=0.0s: A 开始执行
    # T=0.1s: A 完成。B 和 C 同时开始并发执行
    # T=0.2s: B 和 C 都完成。D 开始执行
    # T=0.3s: D 完成。总耗时应在 0.3s 左右。
    test_dag = {"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]}

    start_time = time.time()
    results = await execute_dag(test_dag)
    total_time = time.time() - start_time

    # 测试 1：基础核心链路 (Happy Path)
    assert len(results) == 4, "未能返回所有节点的结果"
    assert results["A"] == "RESULT_A"
    assert results["D"] == "RESULT_D"

    # 测试 2：最大化并发校验 (Concurrency Engine)
    # 如果代码写成了串行（A -> B -> C -> D），总耗时将是 0.4s
    # 如果完美实现了 DAG 并发（B 和 C 并行），总耗时应在 0.3s 左右
    print(f"⏱️ DAG执行总耗时: {total_time:.4f} 秒")

    if total_time >= 0.38:
        raise AssertionError(
            "❌ 架构缺陷：你的调度引擎退化成了串行执行！B 和 C 没有实现并发，请检查 `await` 的时机。"
        )
    elif total_time < 0.28:
        raise AssertionError(
            "❌ 灾难级 Bug：耗时过短，说明依赖关系被打破了，下游节点提前偷跑了！"
        )

    print("✅ All Tests Passed! 恭喜 AC！你的调度引擎内核已初具雏形。")


def test_crucible():
    asyncio.run(_async_test_runner())


if __name__ == "__main__":
    test_crucible()
