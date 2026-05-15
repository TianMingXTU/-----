# ================= 0. 知识点与 API 映射 (快思考) =================
"""
【节点 3：混乱深渊与秩序之锁 (threading.Lock / RLock)】

🧠 直觉模型：
- 竞态条件 (Race Condition)：想象一个公共卫生间（共享内存），但门上没有锁。几百个人同时冲进去抢坑位，场面极其混乱（数据被相互覆盖错乱）。
- `Lock` (互斥锁)：这就是门上的物理插销。拿到插销（acquire）的人进去办事，办完拔出插销（release），外面的人只能排队阻塞。
- `RLock` (可重入锁)：想象你身上挂着一把智能万能钥匙。你进大门时锁了一次门，进卧室时又调了同一个上锁方法。如果是普通 `Lock`，你会在卧室门口把自己锁死（死锁）；但 `RLock` 认人，只要是“同一个线程”来请求，你可以无限次开锁进门，只要出来时释放相同次数即可。

🛠️ 核心 API 兵器谱：
- `threading.Lock()` / `threading.RLock()`
- `lock.acquire()` 与 `lock.release()`
- 语法糖防弹衣：`with lock:` (离开上下文自动 release，防死锁神器)
"""

# ================= 1. 依赖导入 (Imports) =================
import threading
import time
from typing import List

# ================= 2. API 实战场 (API Battleground) =================


def api_rookie_mistake() -> None:
    """
    【案发现场/初级代码】
    新手经典死法 1：裸奔的 `counter += 1`。在几万个线程并发下，因为 `+=` 并非原子操作，数据会被严重覆盖。
    新手经典死法 2：用 `acquire()` 上了锁，但中间代码抛出异常崩溃了，没有走到 `release()`，导致整个系统的其他线程永久饿死（死锁）。
    """
    pass


class BankVault:
    def __init__(self):
        self.balance: int = 0
        # TODO 1: 思考这里到底该用 Lock() 还是 RLock()？
        # 提示：看一眼下面的 batch_deposit 方法！
        self.lock = threading.RLock()  # 替换为正确的锁对象

    def deposit(self, amount: int, loops: int) -> None:
        """单笔存钱：必须保证线程安全"""
        # TODO 2: 使用 with 语法糖优雅地上锁，并执行 self.balance += amount
        with self.lock:
            for loop in range(loops):
                self.balance += amount

    def batch_deposit(self, amounts: List[int]) -> None:
        """
        批量存钱：这是一个【原子操作】。
        要求：在把这一批钱全部存完之前，不允许任何其他线程插队修改余额！
        """
        # TODO 3: 上锁保护整个批次循环
        # 注意：这里内部调用的 self.deposit() 也会尝试获取同一把锁！
        # 如果你 TODO 1 选错了锁，这里一旦运行就会发生可怕的死锁。
        for amt in amounts:
            self.deposit(1, amt)


def pythonic_api_engine(vault: BankVault, num_threads: int, loops: int) -> None:
    """
    TODO: 引擎驱动器。你需要在这里创建多线程来疯狂轰炸 BankVault。

    实战要求：
    创建 `num_threads` 个线程，每个线程循环执行 `loops` 次 `vault.deposit(1)`。
    """
    threads = []

    # TODO 4: 编写多线程启动逻辑
    for i in range(num_threads):
        t = threading.Thread(target=vault.deposit, args=(1, loops))
        threads.append(t)
        t.start()

    # TODO 5: 等待所有线程执行完毕
    for t in threads:
        t.join()


# ================= 3. 黑盒测试 (Test Cases：API 严苛审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行 API 级黑盒测试 ---")
    start_time: float = time.time()

    vault = BankVault()

    try:
        # 测试 1: 并发压测 (竞态条件测试)
        print(">> 正在执行高并发轰炸测试 (10 个线程，每个加 10 万次)...")
        pythonic_api_engine(vault, num_threads=10, loops=100000)

        if vault.balance != 1000000:
            raise AssertionError(
                f"❌ 竞态条件发生！期望余额 1000000，实际余额 {vault.balance}。你肯定没有正确加锁！"
            )

        # 测试 2: 可重入死锁测试
        print(">> 正在执行嵌套锁逻辑测试 (批量存款)...")
        test_batch = [100, 200, 300]

        # 开一个独立线程测试批量存款，并设置超时时间防死锁卡死系统
        batch_thread = threading.Thread(target=vault.batch_deposit, args=(test_batch,))
        batch_thread.start()
        batch_thread.join(timeout=2.0)

        if batch_thread.is_alive():
            raise AssertionError(
                "❌ 死锁警告！你使用了 threading.Lock()，导致 batch_deposit() 内部调用 deposit() 时把自己锁死了！"
            )

        if vault.balance != 1000600:  # 之前的 100w + 600
            raise AssertionError("❌ 批量存款逻辑错误或数据丢失！")

    except Exception as e:
        raise AssertionError(f"❌ 熔炉爆炸 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time
    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功驯服了并发数据安全和重入锁！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：API 降维打击) =================
"""
🧠 慢思考拷问 (源码级教官的灵魂一问)：
上一个节点你刚学了 GIL（全局解释器锁），它保证了任何时刻只有一个物理核在执行 Python 字节码。
那么问题来了：

既然 Python 解释器自带 GIL 这个“大锁”，多线程执行代码本来就是排队的，为什么在没有手动加 `self.lock` 的情况下，执行 `self.balance += 1` 依然会发生数据错乱（竞态条件）？
GIL 到底保护了什么？它为什么不保护 `self.balance += 1`？

（提示：去查一下 Python 解释器把 `a += 1` 翻译成了几条基础的汇编/字节码指令，线程是在什么时候被强制切换的？）

👉 回答区：因为+=不是原子语句，而不是三个语句，分为读取、计算、写入三个过程，这三个过程中，只要有其他的线程来进行修改或者读取就会出现问题。+=调用的魔法是__isadd__。
"""
