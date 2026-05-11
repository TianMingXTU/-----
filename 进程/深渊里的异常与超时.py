# ================= 0. 知识点讲解 =================
"""
【深渊里的异常与超时 (Exceptions & Timeouts)】

直觉模型：
子进程就像是派出去执行危险机密任务的特工。如果特工在任务中意外踩雷阵亡（抛出 Exception），他是没办法给总部打电话报错的。
此时，如果你（主进程）在总部傻傻地等他通过加密通道送情报（`queue.get()`），你就会永远等下去，导致总部系统（主进程）发生死锁。

核心陷阱与解法：
1. 异常不冒泡 (Silent Failures)：子进程报错崩溃，主进程默认完全不知道。
   - 解法：在子进程内部使用 `try...except` 拦截所有异常，并将异常信息（最好是字符串形式的堆栈）通过 Queue 发送回主进程。这叫“异常包装协议 (Exception Wrapping Protocol)”。
2. 无限期死等 (Infinite Blocking)：如果子进程进入死循环卡死，或者在发消息前被系统底层的 OOM Killer 爆头，`queue.get()` 会无限阻塞。
   - 解法：必须使用 `queue.get(timeout=N)`。这里会抛出标准库 `queue.Empty` 异常。一旦超时，立刻判定特工失联，触发应急预案（亲手 `terminate` 清理门户，并抛出 Timeout 异常）。
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time
import queue  # ❗️注意：获取超时异常需要标准库的 queue.Empty
import traceback

# ================= 2. 代码骨架 (Starter Code) =================


def fragile_worker(task_id, data, result_queue):
    """
    【业务场景】这是一个极其脆弱的数据处理节点。
    - 如果 data 是负数，它会抛出 ValueError。
    - 如果 data 是 999，它会陷入无限死循环（卡死）。
    """
    try:
        print(f"  [Worker-{task_id}] 开始处理数据: {data}")
        if data < 0:
            raise ValueError(f"检测到非法负数数据: {data}")
        if data == 999:
            time.sleep(100)  # 模拟死循环卡死

        # 正常处理逻辑
        time.sleep(0.1)
        result = data * 2

        # TODO 1: 处理成功，将成功的状态和结果放入 result_queue
        result_queue.put(("SUCCESS", result))

    except Exception as e:
        # TODO 2: 捕获到异常！立刻获取详细的报错堆栈字符串，并放入 result_queue
        error_msg = traceback.format_exc()
        result_queue.put(("ERROR", error_msg))


def robust_dispatcher(task_id, data):
    """
    TODO: 在此实现你的高可用调度逻辑
    要求：
    1. 创建一个 multiprocessing.Queue()。
    2. 启动一个子进程执行 fragile_worker。
    3. 尝试从 Queue 中获取结果，最多等待 1 秒钟 (利用 queue.get 的 timeout 参数)。
    4. 如果超时 (捕获 queue.Empty 异常)：说明子进程卡死了。必须杀掉子进程，并主动抛出 TimeoutError。
    5. 如果拿到结果：
       - 如果是 "ERROR" 状态，主进程必须主动 raise RuntimeError，并带上子进程传来的错误堆栈。
       - 如果是 "SUCCESS" 状态，返回计算结果。
    """
    q = multiprocessing.Queue()
    p = multiprocessing.Process(
        target=fragile_worker, args=(task_id, data, q), daemon=True
    )
    p.start()
    try:
        result = q.get(timeout=1)
        if result[0] == "ERROR":
            raise RuntimeError(result[1])
        else:
            return result[1]
    except queue.Empty:
        p.terminate()
        raise TimeoutError


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    # 测试 1：Happy Path (正常链路)
    try:
        res = robust_dispatcher(1, 10)
        assert res == 20, "正常计算逻辑错误"
        print("✅ 测试 1 通过：正常链路无误。")
    except Exception as e:
        raise AssertionError(f"❌ 测试 1 失败：正常数据不应该抛出异常 {e}")

    # 测试 2：异常穿透拦截 (Exception Propagation)
    try:
        robust_dispatcher(2, -5)
        raise AssertionError(
            "❌ 灾难级 Bug：子进程报错了，主进程居然装作不知道？异常没有穿透！"
        )
    except RuntimeError as e:
        if "非法负数数据" not in str(e):
            raise AssertionError(
                "❌ 错误信息丢失：虽然抛出了 RuntimeError，但没带上子进程的具体报错堆栈！"
            )
        print("✅ 测试 2 通过：成功捕获并重建子进程异常。")

    # 测试 3：死锁阻断 (Timeout & Kill)
    start_t = time.time()
    try:
        robust_dispatcher(3, 999)
        raise AssertionError("❌ 灾难级 Bug：卡死的任务竟然返回了？你没有卡住它！")
    except TimeoutError:
        cost = time.time() - start_t
        if cost > 1.5:
            raise AssertionError(
                "❌ 性能 Bug：你阻塞的时间太长了，timeout 机制未生效！"
            )
        print("✅ 测试 3 通过：成功判定超时并阻断死锁。")

    print("🎉 All Tests Passed! 恭喜 AC！你成功填平了多进程最深的一个坑。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
我们在 TODO 2 中，强烈建议你用 `traceback.format_exc()` 把异常转换成“字符串”再发给主进程，
而不是直接把 `Exception` 对象本身放入 Queue（即避免写成 `result_queue.put(("ERROR", e))` ）。

请在脑海中推演一下：如果你直接把底层的 Exception 对象放进 Queue 传给主进程，可能会引发什么致命灾难？
（提示：多进程 Queue 传递数据的底层原理是什么？异常对象身上可能挂载着什么庞大的、不可理喻的上下文对象？）

回答：异常的对象上面可能含有很大的数据超过内容。Queue的是一个先进先出的数据结构，data存的空间大小应该是分配好的，为了时间效率来说。如果不是分配好的，那么这个节点就要扩容和复制，比较消耗时间。
"""
