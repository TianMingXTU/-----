"""
================= 0. 干活指南与 API 映射 (快思考) =================
【异步控制流：上下文与迭代器】

🧠 实用直觉：
- `async with`：就把它当成普通的 `with`（比如用 `with open(...)` 读文件）。只不过这次打开的是“需要消耗时间建立连接”的资源，比如数据库、Redis、或者 aiohttp 的网络 Session。它能保证不管代码怎么崩，最后都会帮你自动关门（释放连接）。
- `async for`：把它当成普通的 `for` 循环。只不过遍历的数据不是现成存在内存里的，而是“需要花时间从网络/磁盘上一条条等过来”的。

🛠️ 核心 API 兵器谱：
- `async with AsyncContextManager() as resource:` # 安全获取异步资源，自动处理 __aenter__ 和 __aexit__。
- `async for item in async_iterable:`             # 遍历异步数据流，自动处理 __aiter__ 和 __anext__。
"""

# ================= 1. 环境与依赖准备 =================
import asyncio
import time
from typing import Any, AsyncGenerator

# ================= 2. 搬砖实战场 (Pragmatic Battleground) =================


# 🧱 基础设施：我为你封装的一个工业级“伪造异步数据库驱动”
class MockAsyncDB:
    def __init__(self) -> None:
        self.is_connected = False

    # 异步上下文管理：入场
    async def __aenter__(self) -> "MockAsyncDB":
        print("🔗 [DB] 正在异步建立数据库连接 (耗时0.2s)...")
        await asyncio.sleep(0.2)
        self.is_connected = True
        return self

    # 异步上下文管理：退场（极其重要：负责擦屁股释放资源）
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        print(f"🔒 [DB] 正在异步断开数据库连接。是否有异常发生: {exc_type is not None}")
        await asyncio.sleep(0.1)
        self.is_connected = False

    # 异步生成器：模拟流式返回千万级数据，而不是一次性塞爆内存
    async def fetch_stream(self, limit: int) -> AsyncGenerator[dict[str, Any], None]:
        if not self.is_connected:
            raise RuntimeError("数据库未连接！")
        for i in range(1, limit + 1):
            await asyncio.sleep(0.1)  # 模拟网络IO等待下一条数据
            yield {"id": i, "log": f"robot_sensor_data_{i}"}


"""
【案发现场：干活时的低级错误】
错误 1：习惯性写了普通的 `with`，导致报出 `AttributeError: __enter__` 让你怀疑人生。
错误 2：用普通的 `for` 循环去遍历 `fetch_stream`，结果拿到的不是数据，而是一个 `<async_generator object>` 内存地址。
"""


async def rookie_mistake() -> None:
    # ❌ 灾难示范 1：这里绝对不能用普通的 with
    # with MockAsyncDB() as db:
    pass

    # ❌ 灾难示范 2：这里绝对不能用普通的 for
    # for row in db.fetch_stream(5):
    pass


"""
【实战干活：TODO】
背景说明：你的机器人传回了海量的传感器流式日志，存储在远程数据库中。
老板要求：写一个清洗脚本，连接数据库，拉取前 5 条日志，提取每条日志的 "log" 字段并返回。

实战要求：
1. 必须使用 `async with` 安全地开启 `MockAsyncDB` 连接。
2. 必须使用 `async for` 遍历 `fetch_stream(5)` 的结果。
3. 把处理好的日志放入一个列表中并返回。
"""


async def pragmatic_api_engine(limit: int) -> list[str]:
    processed_logs: list[str] = []

    # TODO 1: 使用 async with 实例化并连接 MockAsyncDB，命名为 db_conn
    # 提示代码骨架: async with ... as ... :
    async with MockAsyncDB() as db_conn:

        # TODO 2: 在该上下文中，使用 async for 遍历 db_conn.fetch_stream(limit)
        async for content in db_conn.fetch_stream(limit):
            # TODO 3: 将每一行数据中的 "log" 字段 append 到 processed_logs 中
            processed_logs.append(content["log"])
    # 最终返回处理结果
    return processed_logs


# ================= 3. 黑盒测试 (Test Cases：交差验收) =================
def test_crucible() -> None:
    print("🚀 开始执行流式日志清洗任务...")
    start_time = time.time()

    # 启动事件循环
    results = asyncio.run(pragmatic_api_engine(5))
    cost_time = time.time() - start_time

    print(f"📦 收集到的日志: {results}")
    print(f"⏱️ 耗时: {cost_time:.2f} 秒")

    # 验收断言
    assert len(results) == 5, "❌ 结果数量不对！是否没有正确遍历流式数据？"
    assert results[0] == "robot_sensor_data_1", "❌ 字段提取错误！"
    # 验证是否流式等待（0.2连接 + 5*0.1数据等待 + 0.1断开 ≈ 0.8秒）
    assert 0.7 < cost_time < 1.0, "❌ 时间不对！没有体现出流式 IO 的特征！"

    print("✅ QA 测试通过！资源安全释放，数据精准提取，准备下班。")


if __name__ == "__main__":
    test_crucible()

"""
================= 4. 慢思考 (事后诸葛亮：线上事故复盘) =================
🧠 慢思考拷问：
【真实事故场景模拟】：
这段代码上线跑得很稳。但有一天，传感器传回了一条“脏数据”，导致你的 `TODO 3` 内部抛出了一个极其致命的 `KeyError` 异常，整个 `pragmatic_api_engine` 函数当场崩溃退出。

👉 救火任务："在普通的同步代码中，遇到崩溃，数据库连接往往会变成僵尸连接一直挂在服务器上。但在我们的代码中，哪怕 `async for` 里发生崩溃，数据库连接依然会被安全释放！**请结合底层的 `__aexit__` 机制，告诉我为什么 `async with` 能够在异常崩溃时充当坚不可摧的防线？它和传统的 `try...finally` 有什么关系？**"
回答：aexit其实也是使用了try finally，报错了之后，一定会走finally，关闭连接。
"""
