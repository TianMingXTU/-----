"""
================= 0. 干活指南与 API 映射 (快思考) =================
【超时防御与同步破局】

🧠 实用直觉：
- `wait_for`：异步代码里的“定时炸弹”。绝不允许任何不受信任的外部网络请求无限期等下去。给它定个死线，时间一到直接掐断抛异常。
- `to_thread`：异步世界里的“隔离病房”。遇到那些会卡死主线程的同步代码（如 time.sleep, requests.get, 复杂的矩阵计算），直接用它扔进后台线程池里跑，主事件循环继续去接客。

🛠️ 核心 API 兵器谱：
- `await asyncio.wait_for(aw, timeout: float)` # 给可等待对象上个倒计时，超时抛 TimeoutError。
- `await asyncio.to_thread(func, *args)`       # (Python 3.9+) 将阻塞的同步函数扔进线程池执行并等待结果。
"""

# ================= 1. 环境与依赖准备 =================
import asyncio
import time
from typing import Any

# ================= 2. 搬砖实战场 (Pragmatic Battleground) =================

"""
【案发现场：干活时的低级错误】
错误 1：对不可控的外部 API 直接 await，对方服务器宕机，你的代码永远卡在这一行。
错误 2：在 async def 里面直接调用了耗时的同步函数，导致整个机器人的并发调度系统“心脏骤停”。
"""


async def rookie_mistake() -> str:
    # ❌ 灾难 1：没有超时控制
    # data = await unreliable_sensor_api()

    # ❌ 灾难 2：直接调用同步阻塞代码，此时其他所有 concurrent tasks 都会被卡死
    # result = legacy_heavy_compute(data)
    return "ok"


# 🧱 基础设施 1：模拟一个永远不会回应的传感器 API (死机状态)
async def unreliable_sensor_api() -> str:
    print("🌐 [Network] 正在请求传感器数据...")
    await asyncio.sleep(9999)  # 模拟永远等不到回应
    return "sensor_data_1024"


# 🧱 基础设施 2：模拟一个你无法修改源码的老旧同步函数（例如老旧的机器视觉处理模块）
def legacy_heavy_compute(data: str) -> str:
    print(f"⚙️ [Sync Worker] 开始执行沉重的同步计算: {data}")
    time.sleep(1)  # 真正的同步阻塞！在这 1 秒内，线程被完全占死。
    print(f"⚙️ [Sync Worker] 同步计算完成！")
    return f"processed_{data}"


"""
【实战干活：TODO】
背景说明：你的调度系统需要从一个不稳定的传感器拉取状态，然后丢给一个老旧的同步 C++ 视觉库去处理。
实战要求：
1. 传感器拉取不能死等！给它设定 1.0 秒的超时时间。如果超时，捕获异常，启用备用数据 `"fallback_data"`。
2. 拿到数据后，绝对不能在当前协程直接调用 legacy_heavy_compute（会卡死整个系统），必须把它扔进线程池去跑。
"""


async def pragmatic_api_engine() -> str:
    data: str = ""

    # TODO 1: 尝试 await 拉取 unreliable_sensor_api()。
    # 必须使用 asyncio.wait_for 将其限制在 1.0 秒内。
    # 提示：需要 try...except TimeoutError 来捕获超时，并在 except 块中将 data 赋值为 "fallback_data"。
    try:
        data = await asyncio.wait_for(unreliable_sensor_api(), timeout=1)
    except TimeoutError:
        data = "fallback_data"
    # TODO 2: 现在你有了 data（可能是正常数据，也可能是 fallback_data）。
    # 使用 asyncio.to_thread 调用 legacy_heavy_compute 处理 data，并 await 它的返回值。
    result = await asyncio.to_thread(legacy_heavy_compute,data)
    # 返回最终处理好的字符串
    return result


# ================= 3. 黑盒测试 (Test Cases：交差验收) =================
def test_crucible() -> None:
    print("🚀 开始执行健壮性护航测试...")

    async def main_test() -> None:
        # 启动一个后台心跳任务，用来监测主事件循环是否被恶意的同步代码卡死
        async def heartbeat() -> int:
            ticks = 0
            for _ in range(25):
                await asyncio.sleep(0.1)
                ticks += 1
            return ticks

        hb_task = asyncio.create_task(heartbeat())

        start_time = time.time()
        # 运行你的核心引擎
        result = await pragmatic_api_engine()
        cost_time = time.time() - start_time

        # 等待心跳任务结束
        ticks = await hb_task

        print(f"📦 最终结果: {result}")
        print(f"⏱️ 引擎总耗时: {cost_time:.2f} 秒")
        print(f"💓 后台心跳跳动次数: {ticks} 次")

        # 验收断言
        assert (
            result == "processed_fallback_data"
        ), "❌ 结果错误！你是否没有正确捕获超时并启用 fallback？"
        assert (
            1.9 < cost_time < 2.2
        ), "❌ 时间不对！超时1秒 + 同步计算1秒，总耗时应该在2秒出头！"
        assert (
            ticks >= 15
        ), "❌ 灾难！心跳任务严重丢帧！你肯定在 async 函数里直接执行了同步阻塞代码，导致事件循环(Event Loop)被卡死了！必须用 to_thread 剥离！"

        print(
            "✅ QA 测试通过！你的代码抗住了网络断联和同步阻塞的双重打击，系统依然丝滑。准备下班。"
        )

    # 启动点火
    asyncio.run(main_test())


if __name__ == "__main__":
    test_crucible()

"""
================= 4. 慢思考 (事后诸葛亮：线上事故复盘) =================
🧠 慢思考拷问：
【真实事故场景模拟】：
某个实习生没有用你的这套规范，他直接在 `async def` 里面写了一句 `requests.get("http://slow-api.com")`。
上线后，老板发现整个机器人系统的并发调度“全部僵死”了，明明系统 CPU 占用率几乎为 0，但就是连最简单的“响应前端 Ping 信号”的异步任务都不执行了。

👉 救火任务："在同步编程里，阻塞最多也就是当前线程卡一下。但在协程世界里，为什么一句简单的同步阻塞（如 time.sleep 或 requests.get），会导致系统明明 CPU 很闲，却呈现出全局瘫痪的“植物人”状态？结合事件循环 (Event Loop) 的本质用一句话解释。"
回答：因为事件循环每一次都要重新跑那个同步函数，导致卡死
"""
