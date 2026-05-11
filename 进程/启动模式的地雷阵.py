# ================= 0. 知识点讲解 =================
"""
【启动模式的地雷阵 (fork vs spawn vs forkserver)】

直觉模型：
当你调用 `Process.start()` 时，操作系统究竟是怎么“生”出一个子进程的？
1. fork (Linux 默认): “克隆人”。瞬间复制主进程当前的全部内存状态。极快！省内存 (Copy-on-Write)！
   - 💣 致命死锁陷阱：如果主进程里有其他【线程】正拿着一把锁，fork 出的子进程会继承这把“被锁上”的锁，但不会继承那个释放锁的线程！子进程一旦试图碰那把锁，就会永久死锁。
2. spawn (Windows / macOS 默认): “新生儿”。启动一个全新的 Python 解释器，从头开始导入所有模块。比较慢，但极其干净、安全。
3. forkserver (Linux 可选): 折中方案。程序一启动，先造一个干干净净的“白板进程”。以后每次需要子进程，都从这个白板 fork。既快，又避开了主进程后来的脏状态。

核心语法：
- `multiprocessing.set_start_method('spawn', force=True)`
⚠️ 铁律：这句代码必须在所有多进程逻辑运行前（通常在 `if __name__ == '__main__':` 的最开始）执行！
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import threading
import time
import os

# ================= 2. 代码骨架 (Starter Code) =================

# 模拟一个第三方库（如 logging, gRPC, 数据库底层驱动）内部自己维护的全局锁
third_party_lock = threading.Lock()


def innocent_worker():
    """
    【业务场景】普通的子进程任务，底层不可避免地会调用到第三方库。
    """
    print(f"  [子进程 PID:{os.getpid()}] 准备调用第三方库...")

    # 模拟底层库尝试获取它自己的锁
    # 💥 如果是 'fork' 模式，它会继承父进程已经被锁住的状态，瞬间永久死锁！
    # 🛡️ 如果是 'spawn' 模式，由于是全新导入模块，它会拥有一把全新的、未加锁的 lock。
    acquired = third_party_lock.acquire(timeout=2)

    if acquired:
        print(f"  [子进程 PID:{os.getpid()}] 成功获取底层锁！正常执行完毕。")
        third_party_lock.release()
    else:
        print(f"  [子进程 PID:{os.getpid()}] ❌ 惨遭死锁！根本拿不到锁！")


def engine_setup():
    """
    TODO: 在此配置多进程的启动上下文
    要求：
    如果不做配置，在老版本的 Linux 环境下默认使用 'fork'，本程序必定死锁。
    请强制将启动模式设置为 'spawn'，避开这颗克隆地雷。
    (提示：使用 multiprocessing.set_start_method 并且一定要加上 force=True，防止重复设置报错)
    """
    multiprocessing.set_start_method(method="spawn",force=True)


# --- 💣 案发现场模拟 ---
def simulate_production_crash():
    # 1. 启动你的安全配置
    engine_setup()

    # 2. 模拟主进程中的某个后台监控线程刚好锁住了第三方库
    third_party_lock.acquire()
    print(f"[主进程 PID:{os.getpid()}] 某后台线程刚好占用了第三方库的全局锁...")

    # 3. 此时主进程不知情地创建了子进程
    p = multiprocessing.Process(target=innocent_worker)
    p.start()

    # 4. 主进程故意不释放锁，冷酷观察子进程是否会被牵连死锁
    p.join(timeout=3)

    # 清理现场并收集尸检报告
    alive = p.is_alive()
    if alive:
        p.terminate()  # 超时没执行完，说明死锁了，强杀
        p.join()

    third_party_lock.release()

    return (
        not alive
    )  # 如果进程还活着(卡死了)，返回 False；如果死了(正常结束)，返回 True


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    success = simulate_production_crash()
    total_cost = time.time() - start_time

    if not success:
        raise AssertionError(
            "❌ 灾难级 Bug：子进程死锁了！你没有成功将启动模式切换为 'spawn'。它继承了那把被锁死的锁！"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功跨越了最恶心的操作系统底层地雷。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
你刚才用 `spawn` 模式完美解决了 `fork` 带来的死锁问题。
但是请你在脑海中推演一下另一种工业场景：

假设你在代码的最开头写了一句：`heavy_model = load_ai_model("10GB_大语言模型.pt")` (加载到全局变量里)。
如果你使用 `fork` 模式启动 4 个子进程，它们由于操作系统的“写时复制 (Copy-on-Write)”机制，会瞬间共享这 10GB 内存，内存几乎不增加。
但如果你使用 `spawn` 模式启动 4 个子进程，你的服务器内存会发生什么极其恐怖的事情？为什么？

在 Linux 服务器上，既想避免 `fork` 的死锁，又不想承受 `spawn` 的巨大开销，我们通常会选用哪一种启动模式？（提示：回顾一下知识点讲解）。
回答：使用spawn会将大模型创建到40gb，因为它是干净全新的。使用forkserver这个折中方案。
"""
