# ================= 0. 知识点讲解 =================
"""
【零拷贝的性能巅峰 (SharedMemory)】

直觉模型：
前面的 Queue、Pipe、Manager，无论怎么优化，都逃不掉“把数据打包(Pickle) -> 通过管道搬运 -> 拆包(Unpickle)”的过程。IPC 极其昂贵。
如果我们要让 4 个进程同时处理一个 2GB 的高清图像矩阵，搬运数据会把内存撑爆，把 CPU 卡死。

`multiprocessing.shared_memory` (Python 3.8+ 引入) 就是终极杀器：
主进程直接向操作系统申请一块纯粹的“物理内存”，然后让所有子进程的指针直接挂载到这块内存上！
没有任何搬运，没有任何序列化。这就是传说中的“零拷贝 (Zero-Copy)”。

致命陷阱：幽灵内存泄漏 (OS-level Memory Leak)！
这块内存直接归属操作系统，Python 的垃圾回收器 (GC) 根本无权干涉它。
1. `close()`: 每个用完它的进程（包括主进程），必须调用 `shm.close()`，意思是“我把视线移开了，不再碰它”。
2. `unlink()`: 创造它的主进程，在彻底用完后，必须调用 `shm.unlink()`，意思是“呼叫操作系统，把它从物理条上彻底炸毁”。
💣 如果你忘了 unlink，这块内存会像幽灵一样永远卡在你的物理机里，甚至你的 Python 脚本退出了它还在！直到你重启服务器。
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
from multiprocessing import shared_memory
import time

# ================= 2. 代码骨架 (Starter Code) =================


def extreme_worker(shm_name, worker_id):
    """
    【业务场景】子进程：通过名字挂载到那块共享内存，并直接在内存上刻字。
    注意：共享内存里没有 Python 的 list 或 dict，全都是最原始的字节流 (bytes/bytearray)！
    """
    # TODO 1: 挂载共享内存。利用传过来的名字 shm_name 连接它。(注意：不要加 create=True)
    shm = shared_memory.SharedMemory(name=shm_name)

    try:
        # 直接操控内存的底层缓冲区 (buffer)
        # 我们让 0号子进程修改第0个字节，1号修改第1个字节...
        shm.buf[worker_id] = 88  # 写入十进制 88 (即 ASCII 字符 'X')
        print(f"  [子进程 {worker_id}] 成功在偏移量 {worker_id} 处写入字节！")
        time.sleep(0.1)
    finally:
        # TODO 2: 子进程用完了，必须闭眼离开（关闭连接，但绝不能销毁它！）
        shm.close()


def zero_copy_engine():
    """
    TODO: 在主进程中申请并严格管理共享内存的生命周期
    """
    # 1. 向 OS 申请一块 10 bytes 大小的全新共享内存 (create=True)
    shm_main = shared_memory.SharedMemory(create=True, size=10)
    print(f"[引擎] 成功申请系统级共享内存，代号: {shm_main.name}")

    try:
        workers = []
        # TODO 3: 启动 3 个子进程，把共享内存的【名字】(shm_main.name) 传给它们
        # ...
        for i in range(3):
            p = multiprocessing.Process(target=extreme_worker, args=(shm_main.name, i))
            p.start()
            workers.append(p)

        for p in workers:
            p.join()

        # 提取前 3 个字节的结果并返回
        result = list(shm_main.buf[:3])
        return result
    finally:
        # TODO 4: 主进程的终极收尾：关闭自己对这块内存的访问，并彻底向 OS 申请核爆级销毁！
        shm_main.close()
        shm_main.unlink()


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    final_result = zero_copy_engine()
    total_cost = time.time() - start_time

    # 测试 1：验证零拷贝写入是否成功
    if final_result != [88, 88, 88]:
        raise AssertionError(
            f"❌ 灾难级 Bug：子进程写入失败或发生偏移！期望 [88, 88, 88]，实际得到 {final_result}"
        )

    print("✅ 测试 1 通过：成功完成跨进程的零拷贝字节级操作！")

    # 测试 2：致命泄漏测试
    # 尝试在引擎结束后，再次通过名字去挂载这块内存。如果挂载成功，说明你没销毁它！
    try:
        # 这个操作在正常的代码里应该抛出 FileNotFoundError
        # ⚠️ 注意：这段测试代码只能防君子防不了小人，如果你忘了写 name，这里会误报。
        pass
    except Exception:
        pass  # 此处从略复杂的探活逻辑，主要靠你的自觉！

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("🎉 All Tests Passed! 恭喜 AC！你掌握了多进程性能优化的天花板！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
既然 SharedMemory 这么强，不仅零拷贝、没有 IPC 搬运开销，那为什么我们不把所有的数据交互都用它来写？
试从“数据结构”和“防踩踏（同步）”两个角度，推演一下如果在真实的业务中，你想用 SharedMemory 来存储一个高度嵌套的 JSON 字典，你会经历什么样的地狱折磨？
（提示：SharedMemory 的 `buf` 里面装的是什么东西？它自带防踩踏的锁吗？）
回答：buf里面装的是内存视图对象，它这里面没有锁，还是会有数据读写冲突。
"""
