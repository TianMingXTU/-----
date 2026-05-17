"""
================= 0. 干活指南与 API 映射 (快思考) =================
【同步原语：并发安全与协程通信】

🧠 实用直觉：
- `asyncio.Lock`：异步锁。当多个协程要修改同一个全局变量或写入同一个文件时，把它当成“厕所门上的锁”。谁拿到了谁进去（async with），别人就在外面排队（挂起）。
- `asyncio.Event`：异步信号枪。当多个协程需要等待某一个前置条件（比如“硬件初始化完毕”）才能开工时，大家一起 `await event.wait()`。条件满足后，主控发令 `event.set()`，所有人同时冲线。

🛠️ 核心 API 兵器谱：
- `lock = asyncio.Lock()`
  `async with lock:`                      # 获取锁，安全操作共享资源
- `event = asyncio.Event()`
  `await event.wait()`                    # 阻塞等待信号
  `event.set()`                           # 发射信号，唤醒所有等待者
"""

# ================= 1. 环境与依赖准备 =================
import asyncio
import time

# ================= 2. 搬砖实战场 (Pragmatic Battleground) =================

"""
【案发现场：干活时的低级错误】
错误 1：多协程修改全局状态时不加锁，导致数据被相互覆盖（经典的丢失更新问题）。
错误 2：用 `while not ready: await asyncio.sleep(0.1)` 来轮询等待某个状态，白白浪费 CPU 性能。
"""

# 🧱 基础设施：机器人的全局状态面板
robot_state = {"total_tasks_executed": 0}

"""
【实战干活：TODO】
背景说明：你的机器人本体（包含 3 个并发的机械臂子任务）刚刚启动。它们必须等待底层的“视觉传感器初始化”完成后，才能开始各自的任务，并且在完成任务后，安全地更新全局计数器。
实战要求：
1. 必须使用 `asyncio.Event` 来让 3 个子任务挂起，等待视觉传感器的启动信号。
2. 必须使用 `asyncio.Lock` 来保护 `robot_state["total_tasks_executed"]` 的自增操作，防止并发覆盖。
"""

# 全局同步原语（在实际工程中通常封装在类中，这里为了演示定义在全局）
vision_ready_event = asyncio.Event()
state_lock = asyncio.Lock()


# 基础部件：模拟机械臂的工作协程
async def arm_worker(arm_id: int) -> None:
    print(f"🦾 [Arm {arm_id}] 启动就绪，等待视觉传感器发车信号...")

    # TODO 1: 在这里阻塞等待，直到 vision_ready_event 被设置为 True
    vision_ready_event.wait()

    print(f"🦾 [Arm {arm_id}] 收到视觉信号，开始执行夹取任务！")
    await asyncio.sleep(0.1)  # 模拟干活耗时

    # TODO 2: 安全地将 robot_state["total_tasks_executed"] 加 1
    # 提示：即使只是简单的 +1，在复杂的上下文中，await 切换也可能打断它。请使用 async with 加锁。
    async with state_lock:
        robot_state["total_tasks_executed"] += 1

    print(f"🦾 [Arm {arm_id}] 任务完成！")


# 核心引擎：系统主控
async def pragmatic_api_engine() -> None:
    # 把三个机械臂任务扔进后台
    arms = [asyncio.create_task(arm_worker(i)) for i in range(1, 4)]

    print("🧠 [Main] 正在进行视觉传感器硬件自检...")
    await asyncio.sleep(0.5)  # 模拟硬件初始化耗时
    print("🧠 [Main] 视觉传感器初始化完毕！发射信号枪！")

    # TODO 3: 发射信号，唤醒所有正在等待的 arm_worker
    vision_ready_event.set()

    # 等待所有机械臂干完活
    await asyncio.gather(*arms)


# ================= 3. 黑盒测试 (Test Cases：交差验收) =================
def test_crucible() -> None:
    print("🚀 开始执行机器人并发安全测试...")
    robot_state["total_tasks_executed"] = 0

    start_time = time.time()
    asyncio.run(pragmatic_api_engine())
    cost_time = time.time() - start_time

    print(f"📦 最终全局计数: {robot_state['total_tasks_executed']}")
    print(f"⏱️ 引擎总耗时: {cost_time:.2f} 秒")

    # 验收断言
    assert (
        robot_state["total_tasks_executed"] == 3
    ), "❌ 计数错误！你肯定没加锁导致数据丢失了！"
    assert (
        0.5 < cost_time < 0.7
    ), "❌ 时序错误！机械臂没有真正实现并发等待，或者发车信号没写对！"

    print("✅ QA 测试通过！你的机器人并发调度系统坚如磐石。完美结业。")


if __name__ == "__main__":
    test_crucible()

"""
================= 4. 慢思考 (事后诸葛亮：线上事故复盘) =================
🧠 慢思考拷问：
【真实事故场景模拟】：
系统平稳运行了几个月。某天，因为业务逻辑极其复杂，你在 `arm_worker` 的锁内部（`async with state_lock:` 块中）调用了一个非常深层的函数，而那个函数内部居然又尝试获取了一次 `state_lock`！
代码上线后，机器人直接死机（Deadlock），整个系统僵死，所有后续任务全部卡在等锁的地方。

👉 救火任务："在 Java 或 C++ 中，很多锁是『可重入锁』（ReentrantLock，即同一个线程可以多次获取同一把锁）。但去查一下 Python 官方文档，**`asyncio.Lock` 是可重入的吗？结合这种死锁事故，你在工程实践中应该如何避免在锁内部进行复杂的异步调用？**"
回答：不是，只有RLock才是。确保锁内部不要嵌套锁。
"""
