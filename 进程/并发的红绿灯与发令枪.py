# ================= 0. 知识点讲解 =================
"""
【并发的红绿灯与发令枪 (Event & Semaphore)】

直觉模型：
1. Event (事件/发令枪)：
   想象田径赛场上，8个运动员（子进程）已经蹲在起跑线上。他们不能直接跑，必须死等发令枪响。
   主进程就是裁判。裁判扣动扳机（`event.set()`），所有运动员瞬间同时起跑。
   如果后面还有多轮比赛，裁判可以重置发令枪（`event.clear()`）。
   - 运动员动作：`event.wait()` (死等枪响)
   - 裁判动作：`event.set()` (开枪)

2. Semaphore (信号量/闸机)：
   比赛跑到一半，遇到一个独木桥，桥上最多只能同时过 2 个人。
   这叫“并发限流”。它就像一个拥有 N 把钥匙的 Lock（普通的 Lock 相当于只有 1 把钥匙的 Semaphore）。
   - 运动员动作：`with semaphore:` (抢钥匙，抢不到就在桥头阻塞死等)
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time
import os

# ================= 2. 代码骨架 (Starter Code) =================


def athlete_worker(athlete_id, start_gun, bridge_gate, result_queue):
    """
    【业务场景】运动员进程：听枪声起跑，然后过独木桥。
    """
    print(f"  [运动员 {athlete_id}] 已就位，等待发令枪...")

    # TODO 1: 阻塞等待发令枪响
    start_gun.wait()

    print(f"  [运动员 {athlete_id}] 听见枪响！冲向独木桥！")

    # TODO 2: 独木桥限流。必须抢到闸机许可才能上桥
    # 提示：请使用上下文管理器 with ...
    # 抢到许可后，执行以下过桥逻辑：
    with bridge_gate:
        print(f"    [运动员 {athlete_id}] 正在过桥...")
        time.sleep(0.5)  # 模拟过桥耗时
        result_queue.put(time.time())  # 记录自己过桥完毕的时间戳


def race_commander():
    """
    TODO: 实现比赛调度
    """
    # 1. 准备道具
    start_gun = multiprocessing.Event()

    # TODO 3: 创建一个容量为 2 的信号量闸机 (Semaphore)
    bridge_gate = multiprocessing.Semaphore(2)

    result_queue = multiprocessing.Queue()
    athletes = []

    # 2. 运动员进场 (3个运动员参加比赛)
    for i in range(3):
        p = multiprocessing.Process(
            target=athlete_worker, args=(i, start_gun, bridge_gate, result_queue)
        )
        p.start()
        athletes.append(p)

    print("[裁判] 所有运动员就位，准备开枪...")

    # 裁判故意拖延 0.5 秒。如果运动员提前跑了，说明 Event 没拦住。
    time.sleep(0.5)

    print("[裁判] 砰！(开枪)")
    # TODO 4: 扣动发令枪，让所有蹲守的运动员同时起跑
    start_gun.set()

    for p in athletes:
        p.join()

    # 3. 收集成绩并返回
    finish_times = []
    while not result_queue.empty():
        finish_times.append(result_queue.get())
    return finish_times


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    finish_times = race_commander()
    total_cost = time.time() - start_time

    if len(finish_times) != 3:
        raise AssertionError("❌ 灾难级 Bug：有运动员失踪了！过桥数据丢失。")

    # 核心测试逻辑推演：
    # 裁判拖延 0.5s -> 运动员 0, 1 过桥 (耗时 0.5s) -> 运动员 2 过桥 (耗时 0.5s)
    # 总耗时应该在 1.5s 左右。
    # 且第一批过桥的人和最后一个人过桥的时间差，应该是 0.5s 左右。
    time_diff = max(finish_times) - min(finish_times)

    print(f"⏱️ 比赛总耗时: {total_cost:.4f} 秒")
    print(f"⏱️ 首尾撞线时间差: {time_diff:.4f} 秒")

    if total_cost < 1.0:
        raise AssertionError(
            "❌ 抢跑或超载：总耗时太短！要么 Event 没拦住，要么 Semaphore 没发挥限流作用（3人同时过桥了）。"
        )

    if time_diff < 0.3:
        raise AssertionError(
            "❌ 闸机失效：首尾撞线时间差几乎为 0，说明 3 个运动员同时过桥了！检查你的 Semaphore 逻辑！"
        )

    print("✅ All Tests Passed! 恭喜 AC！你掌握了精准的并发起跑与限流。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
很多人初学并发时，会天真地想：“既然 Lock 也能阻塞，那我为什么不用 Lock 来当发令枪？”
（思路是：裁判先 acquire 一把锁，然后让所有运动员去抢这把锁。裁判宣布起跑时，把锁 release，运动员抢到锁就跑）。

请在脑海中推演一下：用 `Lock` 代替 `Event` 做发令枪，在上面的 3 个运动员场景中，
起跑的瞬间会发生什么违背“公平竞技”原则的诡异现象？
为什么 `Event` 是发令枪，而 `Lock` 永远成不了发令枪？

回答：我认为Lock是类似于串行的吧，先有锁的运动员就跑了，不公平。Event是广播通知的。

"""
