# ================= 0. 知识点与 API 映射 (快思考) =================
"""
【节点 5 & 7：现代兵器与终局实战 (ThreadPoolExecutor 调度器)】

🧠 直觉模型：

如果说前几个节点教你的是如何一砖一瓦地盖房子，那么 `ThreadPoolExecutor` 就是直接交给你一家高度自动化的“建筑公司”。
- `Executor` (线程池)：自动管理工人（线程）的生老病死。你只需告诉它 `max_workers`（最多雇几个人）。
- `submit()`：你作为包工头，只管把图纸（函数和参数）扔给建筑公司。公司会返回给你一张“工程进度查询单”。
- `Future` 对象：就是那张“查询单”。你可以随时拿着单子去问“建好了没？”(`done()`)，或者死等它建完拿钥匙 (`result()`)。
- `as_completed()`：这是一个魔法收发室。你把手里 100 张查询单全部交进去，哪个工程先建完，收发室就先把你那张单子吐出来，**绝对不按提交的顺序**，而是谁快谁先出。

🛠️ 核心 API 兵器谱：
- `from concurrent.futures import ThreadPoolExecutor, as_completed`
- `with ThreadPoolExecutor(max_workers=N) as executor:`
- `future = executor.submit(fn, *args, **kwargs)`
- `future.result(timeout=None)`: 提取结果，如果在子线程中引发了异常，在此刻会被重新抛出！
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# ================= 2. API 实战场 (API Battleground) =================


def api_rookie_mistake() -> None:
    """
    【案发现场/初级代码】
    新手死法 1：只管 `submit` 不管 `result()`。子线程里的 LLM API 报了 500 错误崩溃了，主线程一无所知，最后发现数据少了一大半（静默失败）。
    新手死法 2：使用 `for future in futures:` 顺序遍历 `result()`。如果第一个任务卡了 10 秒，即使后面的任务早就完成了，主线程也拿不到，丧失了并发响应的意义。
    """
    pass


def llm_api_mock_request(prompt: str) -> str:
    """
    模拟一个不稳定的大语言模型 (LLM) API 请求。
    耗时在 0.1 到 0.5 秒之间波动。有一定的概率会抛出限流异常。
    """
    time.sleep(random.uniform(0.1, 0.5))
    if "error" in prompt:
        raise ConnectionError(f"API Rate Limit Exceeded for prompt: {prompt}")
    return f"Response to [{prompt}]: Success"


def pythonic_api_engine(prompts: List[str], max_workers: int) -> Dict[str, Any]:
    """
    TODO: 编写 LLM API 高并发请求调度器。

    实战要求：
    1. 使用 `with ThreadPoolExecutor(...)` 管理线程池。
    2. 将所有 prompts 提交给线程池。
    3. 巧妙使用字典 (如 `future_to_prompt = {future: prompt}`) 来映射 Future 和原始 prompt，以便后续知道是哪个任务报错了。
    4. 使用 `as_completed` 乱序收割结果。
    5. 如果正常完成，将结果加入成功列表；如果抛出 `ConnectionError`，捕获它并记录在失败列表。
    6. **不用加任何锁**来记录成功/失败状态（思考：为什么主线程收集结果时不需要加锁？）。
    """
    results_report: Dict[str, Any] = {
        "success_count": 0,
        "failed_count": 0,
        "failed_prompts": [],
    }

    # TODO 1: 实例化线程池并提交流程
    with ThreadPoolExecutor(max_workers) as excutor:
        # TODO 2: 创建 future_to_prompt 映射字典
        futures = []
        future_to_prompt = {}  # {future: prompts}
        for prompt in prompts:
            future = excutor.submit(llm_api_mock_request, prompt)
            future_to_prompt[future] = prompt
            futures.append(future)
        # TODO 3: 使用 as_completed 遍历已完成的 future
        for future in as_completed(futures):
            # TODO 4: 安全调用 future.result()，并更新 results_report
            try:
                result = future.result()
                results_report["success_count"] += 1
            except Exception as e:
                results_report["failed_count"] += 1
                results_report["failed_prompts"].append(future_to_prompt)

    return results_report


# ================= 3. 黑盒测试 (Test Cases：API 严苛审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行 API 级黑盒测试 ---")

    test_prompts = [f"Task_prompt_{i}" for i in range(15)]
    # 注入 3 个必定失败的毒药 prompt
    test_prompts.extend(["error_trigger_1", "error_trigger_2", "error_trigger_3"])
    random.shuffle(test_prompts)  # 打乱顺序

    start_time: float = time.time()

    try:
        report = pythonic_api_engine(test_prompts, max_workers=5)
    except Exception as e:
        raise AssertionError(f"❌ API 调用直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 校验数据完整性与异常捕获
    if report["success_count"] != 15:
        raise AssertionError(
            f"❌ 成功数量统计错误！应为 15，实为 {report['success_count']}"
        )
    if report["failed_count"] != 3:
        raise AssertionError(
            f"❌ 异常捕获失效！应拦截 3 个限流错误，实为 {report['failed_count']}"
        )

    # 并发性能断言：
    # 18 个任务，平均 0.3s。如果不并发需 5.4s。
    # 5 个 Worker 并发，理论最慢约 1.5s - 2.0s 之间。
    if total_cost > 2.5:
        raise AssertionError(
            f"❌ 线程池失效：总耗时 {total_cost:.2f}s，你的并发引擎退化成了串行！"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print(
        f"📊 报告总览: 成功 {report['success_count']} 笔, 失败 {report['failed_count']} 笔"
    )
    print("✅ All Tests Passed! 恭喜 AC！你已经彻底掌握了现代 Pythonic 并发兵器！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：API 降维打击) =================
"""
🧠 慢思考拷问 (源码级教官的灵魂一问)：
恭喜你抵达终点，这是最后一个关于 CPython 源码底层调度的问题：

在使用 `with ThreadPoolExecutor(...) as executor:` 语法时，当 `with` 代码块结束时，Python 底层会自动调用 `executor.shutdown(wait=True)`。
请结合你对 Future 对象以及系统调度的直觉推演：

1. 如果我向线程池提交了 100 个大模型请求任务，此时有 5 个正在执行（Worker 正在跑），95 个还在队列里排队。突然主程序因为某种业务原因，想要立刻停止整个系统（比如触发了报警，退出了 `with` 块）。
   默认的 `shutdown(wait=True)` 会怎么对待那 5 个正在执行的任务？又会怎么对待那 95 个还在排队的任务？

2. 如果我想实现“立刻拉闸，排队的任务直接取消掉，不等了”，你需要对 Future 对象执行什么方法？

👉 回答区：应该是等待那5个任务完成，将95个任务取消。
2、使用future.cancel
"""
