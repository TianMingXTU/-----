# ================= 0. 知识点讲解 =================
"""
【多进程生命周期边界 (Lifecycle Control)】

直觉模型：
主进程（老板）招了两个子进程（员工）。
1. 守护进程 (Daemon Process)：类似“保安”。老板下班关门了，保安必须立刻跟着强制下班，不能一个人留在公司。特点：主进程结束时，自动被系统绞杀。
2. 普通进程 (Non-daemon Process)：类似“外包项目组”。老板下班了，项目没写完他们还在干，除非老板显式地“开除”他们。

核心语法与状态监控：
- p.daemon = True (❗️必须在 p.start() 之前设置)
- p.terminate()：老板发送解雇通知书（SIGTERM 信号），强制终止子进程。
- p.kill()：极其暴力的物理拔线（SIGKILL 信号，Python 3.7+ 支持）。
- p.join(timeout=N)：老板最多等你 N 秒。时间一到，如果子进程没跑完，主进程不再挂起继续往下走（❗️注意：join 超时并不会杀掉进程，只会让主进程解除阻塞）。
- p.exitcode：验尸报告。
    * None: 进程还活着
    * 0: 正常执行完毕
    * -N: 被信号 N 杀死了 (比如被 terminate 通常返回 -15)
    * >0: 抛出异常退出了
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time
import os

# ================= 2. 代码骨架 (Starter Code) =================


def heartbeat_worker():
    """
    【业务场景】这是一个心跳上报服务，每秒发一次心跳。
    它应该是一个无限循环。但一旦主进程退出，它必须立刻跟着死掉，绝对不能变成孤儿进程。
    """
    print(f"  [心跳服务 PID:{os.getpid()}] 启动！开始无限监控...")
    try:
        while True:
            print(f"  [心跳服务] 扑通... 扑通...")
            time.sleep(1)
    except Exception:
        pass


def stuck_calculation():
    """
    【业务场景】这是一个极度耗时、可能卡死的复杂计算。
    主进程只给它 2 秒钟时间。如果算不完，主进程必须亲手杀了它。
    """
    print(f"  [计算引擎 PID:{os.getpid()}] 启动！开始执行 10 秒的复杂计算...")
    time.sleep(10)  # 模拟卡死
    print(f"  [计算引擎] 计算完成！(这句话绝对不应该被打印出来)")


def target_function():
    """
    TODO: 在此实现你的生命周期调度逻辑
    要求：
    1. 启动 heartbeat_worker，要求它与主进程“同生共死”（守护进程）。
    2. 启动 stuck_calculation，作为普通进程。
    3. 主进程最多等待 stuck_calculation 2秒钟 (提示：利用 join 的 timeout 参数)。
    4. 2秒后主进程苏醒，如果发现 stuck_calculation 还没死，立刻拔网线（杀死它）。
    5. 杀死之后，记得睡个 0.1 秒等操作系统收尸，然后收集它的验尸报告 (exitcode)。
    6. return 它的 exitcode。
    """
    p1 = multiprocessing.Process(target=heartbeat_worker, daemon=True)
    p2 = multiprocessing.Process(target=stuck_calculation)

    p1.start()
    p2.start()

    p2.join(timeout=2)

    print(f"主进程:{p2.exitcode}")

    if p2.exitcode is None:
        p2.terminate()
        time.sleep(0.1)
        print(f"主进程完成:{p2.exitcode}")
    return p2.exitcode


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    exit_code = target_function()
    total_time = time.time() - start_time

    # 测试 1：耗时拦截 (Timeout Engine)
    print(f"⏱️ 主进程总耗时: {total_time:.4f} 秒")
    if total_time >= 3.0:
        raise AssertionError("❌ 灾难级 Bug：你没有成功阻断超时任务！主进程被卡死了。")
    elif total_time < 1.8:
        raise AssertionError("❌ 调度错误：你是不是根本没有等它 2 秒就直接把它杀了？")

    # 测试 2：验尸报告 (Exitcode Check)
    print(f"📊 计算引擎的验尸报告 (exitcode) = {exit_code}")
    if exit_code == 0:
        raise AssertionError(
            "❌ 逻辑错误：计算引擎竟然正常结束了？你一定是没有杀死它！"
        )
    elif exit_code is None:
        raise AssertionError(
            "❌ 僵尸进程警告：exitcode 为 None 说明它还活着！杀手行动失败。"
        )

    print("✅ All Tests Passed! 恭喜 AC！你掌握了生杀大权。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
在你的代码里，你成功用 `terminate()` 杀死了计算引擎。
但是，请在脑海中推演一下：如果这个计算引擎在被强制杀死的瞬间，正好掌握着我们上一关讲的 `Lock()`（进程锁），
或者正在向 `Queue` 里写数据写到一半... 它被瞬间爆头了，那把锁还会被归还吗？传送带里的数据会损坏吗？

如果你的答案是“锁不会归还/数据会损坏”，那你认为在工业生产中，直接调用 `terminate()` 是一件安全的事情吗？
如果它不安全，我们该如何通知它“优雅地下班”？（提示：回忆上一关我们用来解决 Queue 阻塞的东西）。

我认为是锁不会归还/数据会损坏，我的想法是使用一个标识符，比如none，告诉进程他的生命周期到此结束，然后他就开始释放资源，最后被系统杀死。
"""
