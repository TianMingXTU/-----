# ================= 0. 知识点讲解 =================
"""
【进程池的工程形态 (ProcessPoolExecutor)】

直觉模型：
手写 Process 就像是“接客一次，专门雇一个人，干完活立刻解雇”。频繁的招人（fork/spawn）和解雇（销毁内存）成本极高。
进程池 (Pool) 就像是“包身工团队”。你提前雇好 4 个人（max_workers=4），丢给他们 10000 个任务。谁先干完手头的，就自动去领下一个。

核心语法与概念 (concurrent.futures)：
1. 打造池子：`with ProcessPoolExecutor(max_workers=N) as executor:` (离开 with 代码块时，会自动等所有人下班)。
2. 派发单任务：`future = executor.submit(func, arg1, arg2)`
   - 什么是 Future (期权/凭证)？这说明任务交出去了，但结果还没出来。你可以拿着这个凭证先去干别的。
3. 动态收割：`for future in as_completed(futures_list):`
   - 只要有任意一个任务干完了，这行代码就会立刻把它的凭证吐出来。谁先做完收谁，绝不傻等！
4. 批量派发：`results = executor.map(func, iterable, chunksize=N)` (类似于内置的 map，但它是并发的)。
"""

# ================= 1. 依赖导入 (Imports) =================
import concurrent.futures
import time
import os
import random

# ================= 2. 代码骨架 (Starter Code) =================


def parse_log_file(file_id):
    """
    【业务场景】这是一个模拟的日志解析任务。
    每个文件的解析耗时不一样，有的快（0.1s），有的慢（0.5s）。
    """
    # 模拟随机的 I/O 或计算耗时
    cost = random.uniform(0.1, 0.5)
    time.sleep(cost)

    # 返回解析结果（格式：文件ID，处理该任务的进程PID，耗时）
    return file_id, os.getpid(), cost


def log_processing_engine(num_files):
    """
    TODO: 在此实现你的高并发池化调度引擎
    要求：
    1. 创建一个最大容纳 3 个 worker 的进程池。 (必须使用 with 语法管理生命周期)
    2. 将 num_files 个日志解析任务 (parse_log_file) 提交给进程池。
    3. 利用 as_completed 机制，谁先解析完，就立刻打印谁的结果，并收集到列表中。
    """
    results = []

    # TODO 1: 打造容量为 3 的 ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as executor:

        # TODO 2: 循环提交任务，并将返回的 Future 凭证保存到一个列表中
        futures = []
        for i in range(num_files):
            future = executor.submit(parse_log_file, i)
            futures.append(future)

        print("[引擎] 任务已全部提交！打工人正在疯狂解析...")

        # TODO 3: 动态收割！使用 concurrent.futures.as_completed 遍历这些凭证
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            print(
                f"  [收割] 文件 {res[0]} 解析完毕! (PID: {res[1]}, 耗时: {res[2]:.2f}s)"
            )
            results.append(res)

    return results


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    # 派发 10 个文件解析任务
    final_results = log_processing_engine(10)
    total_cost = time.time() - start_time

    # 测试 1: 数据完整性
    if len(final_results) != 10:
        raise AssertionError("❌ 灾难级 Bug：你漏掉了任务，或者有些期权没有被收割！")

    # 测试 2: 进程池复用性验证
    pids_used = set([res[1] for res in final_results])
    print(f"📊 参与干活的独立进程数: {len(pids_used)} (PID集合: {pids_used})")
    if len(pids_used) > 3:
        raise AssertionError(
            "❌ 配置失控：你明明只雇了 3 个人，怎么会有超过 3 个的 PID？池子炸了！"
        )

    # 测试 3: as_completed 无序性验证 (核心重点)
    # 因为任务耗时随机，先提交的任务不一定先完成。as_completed 必须是无序返回的。
    file_ids = [res[0] for res in final_results]
    if file_ids == list(range(10)):
        print(
            "⚠️ 警告：你的返回顺序竟然是完美的 0 到 9？如果你不是用了 map 而是 as_completed，且耗时是随机的，这几乎不可能。请确认你没有用错 API！"
        )
    else:
        print("✅ 乱序收割验证通过：先完成的任务被优先处理了。")

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("🎉 All Tests Passed! 恭喜 AC！你掌握了现代并发调度的心法。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
假设你现在有 1,000,000 (一百万) 个超级微小的任务（比如只是给一个数字加 1）。
如果你像 TODO 2 里那样，写一个 `for` 循环，调用了 1,000,000 次 `executor.submit()`。

请在脑海中推演：这个代码跑起来，可能会比你写一个单进程（不用多进程）去 for 循环执行**还要慢上百倍**，甚至直接把服务器内存干崩溃。
结合我们前面学过的 Queue 和 Pipe 的底层知识，想想每一次 `submit`，主进程和子进程之间发生了什么昂贵的操作？
如果你必须用多进程处理这一百万个微小任务，该怎么优化？（提示：回顾一下知识点讲解中提到的批量派发 API 里的特殊参数）。

回答：我认为它是创建了太多的进程，创造需要时间，同时，它解决了锁的机制，应该也是类似于Queue那种，也就是加了锁的那种，变成局部串行了。不知道怎么优化。

"""
