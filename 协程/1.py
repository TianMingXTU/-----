"""
================= 0. 干活指南与 API 映射 (快思考) =================
【协程与并发】

🧠 实用直觉：
不要去管什么“生成器”、“底层事件循环挂起”。你就记住：
遇到网络请求/磁盘IO -> 加上 `await` 让它滚去旁边等，别卡住主线程。
想让多个任务一起跑 -> 用 `create_task` 包装好，再扔进 `gather` 里面一把梭。

🛠️ 核心 API 兵器谱：
- `async def func() -> ReturnType`                # 定义一个能被打断的异步函数。
- `await awaitable_obj`                           # 交出控制权，等它干完再往下走。
- `asyncio.run(main_coro)`                        # 发动机点火，只能在最外层（同步环境中）调一次！
- `asyncio.create_task(coro) -> asyncio.Task`     # 把协程丢进后台，立刻开始排队调度。
- `asyncio.gather(*aws, return_exceptions=False)` # 打包多个异步任务并行执行，按顺序收集结果。
"""

# ================= 1. 环境与依赖准备 =================
import asyncio
import time
from typing import Any

# ================= 2. 搬砖实战场 (Pragmatic Battleground) =================

"""
【案发现场：干活时的低级错误】
错误 1：在 async 函数里用了同步阻塞的 time.sleep()，直接把整个事件循环卡死，并发变成串行。
错误 2：漏写了 await，直接返回一个 `<coroutine object ...>` 给上游，业务当场崩溃。
"""


async def rookie_mistake(uid: int) -> dict[str, Any]:
    print(f"开始获取用户 {uid}")
    time.sleep(1)  # ❌ 灾难！这里绝对不能用阻塞的 time.sleep，必须换成异步休眠！
    return {"uid": uid, "status": "ok"}


"""
【实战干活：TODO】
背景说明：接到了一个真实的工业级业务需求：
老板给了你一批用户 ID，让你通过第三方 API 并发获取用户详情。

实战要求：
1. 模拟网络请求：必须手写完成伪造的异步抓取函数 `mock_fetch_user`。
2. 并发调度：在 `pragmatic_api_engine` 中，必须使用 create_task 和 gather 实现真正的并发。
3. 健壮性：哪怕其中一个用户的请求抛出了异常，其他请求也必须正常返回（提示：仔细看 gather 的文档说明）。
"""


# 基础部件：请完成这个模拟异步 IO 的函数
async def mock_fetch_user(uid: int) -> dict[str, Any]:
    # TODO 1: 模拟耗时 1 秒的网络 IO（注意：用正确的 asyncio API 休眠）
    await asyncio.sleep(1)

    # 模拟业务异常：假设 uid 为 404 的用户会触发网络崩溃
    if uid == 404:
        raise ValueError(f"User {uid} not found!")

    return {"uid": uid, "data": f"user_profile_{uid}"}


# 核心引擎：请完成这个并发批处理逻辑
async def pragmatic_api_engine(uids: list[int]) -> list[Any]:
    tasks: list[asyncio.Task] = []

    # TODO 2: 遍历 uids，将 mock_fetch_user 包装成 Task 并塞入 tasks 列表
    for u in uids:
        task = asyncio.create_task(mock_fetch_user(u))
        tasks.append(task)

    # TODO 3: 调用 gather 并发执行所有 task。
    # 核心考点：如何保证当 uid=404 报错时，不影响其他正常 uid 的结果收集？
    result = await asyncio.gather(*tasks, return_exceptions=True)
    return result


# ================= 3. 黑盒测试 (Test Cases：交差验收) =================
def test_crucible() -> None:
    uids_to_fetch = [101, 102, 404, 103]
    print("🚀 开始执行批量拉取任务...")

    start_time = time.time()

    # 启动事件循环
    results = asyncio.run(pragmatic_api_engine(uids_to_fetch))
    cost_time = time.time() - start_time

    print(f"📦 收到结果: {results}")
    print(f"⏱️ 耗时: {cost_time:.2f} 秒")

    # 验收断言
    assert cost_time < 1.5, "❌ 性能不达标！你的代码绝对是串行执行的！"
    assert len(results) == 4, "❌ 结果数量不对！是否因为某个异常导致整个任务树崩塌了？"

    print("✅ QA 测试通过！代码成功合入主分支，准备下班。")


if __name__ == "__main__":
    test_crucible()

"""
================= 4. 慢思考 (事后诸葛亮：线上事故复盘) =================
🧠 慢思考拷问：
【真实事故场景模拟】：
你的代码跑通了，测试耗时1秒多，老板很开心，于是立马上了生产环境，并给你传了一个包含 1,000,000 个 UID 的列表。
代码一运行，数据库瞬间报警，第三方 API 供应商直接把你的服务器 IP 封禁了，系统报出 `Too many open files` 异常，紧接着服务器内存 OOM 崩溃。

👉 救火任务："别慌！别看 create_task 和 gather 写起来这么爽，结合刚才的事故，你觉得 `asyncio.gather` 到底在底层干了什么没有节制的事情？如果要防范这种洪峰流量，你应该在第五阶段的地图里找哪个工具来锁住喉咙？"
回答：我觉得gather构建的是一个队列，它将所有的协程对象构建好了之后才能跑，导致OOM，我觉得应该要采用事件或者是信号量那种机制，控制每一次跑的数量。
"""
