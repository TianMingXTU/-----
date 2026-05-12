# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【内置容器时间常数：不是所有的 O(1) 都生而平等】

直觉模型：

- `list`: 像一排紧凑的储物柜。按门牌号（索引）拿东西极快（常数极小），但要在里面找某个人（`in` 操作），只能从头走到尾。
- `set` / `dict`: 像一个带有智能指纹锁的巨型散列仓库。虽然查找也是“瞬间”（理论上的 $O(1)$），但每次都需要计算指纹（Hash），并处理可能的指纹碰撞（Hash Collision）。它的 $O(1)$ 常数，远大于数组的按索引访问。

致命陷阱/核心武器：
坑 1：在 `list` 中高频使用 `in`。当规模达到百万级时，一次判断就要扫描上百万次内存！
坑 2：以为 `set` 永远是无敌的。如果你的数据量很小（比如只有 10 个元素），把它们转成 `set` 再查找的耗时，反而比直接在 `list` 里找要长（因为建表的 Hash 开销超过了遍历开销）。
武器：大 O 渐进曲线探测器（能自动跑多个 $N$ 并输出增长倍率）。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import tracemalloc
import random
from typing import Callable, Any, List, Set

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def scaling_benchmark(n_scales: List[int]) -> Callable:
    """
    TODO: 在此实现你的【规模拟合压测器】 (战役零核心交付物)
    要求：
    1. 接收一个 N 的列表（如 [1000, 10000, 100000]）。
    2. 对原函数依次传入不同的 N 进行压测。
    3. 打印出随着 N 增加（如 10 倍增长），耗时和内存的【增长倍率】，判断是常数级、线性级还是指数级。
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            print(f"\n--- 📈 开始压测: {func.__name__} ---")
            prev_time = 0.0
            ratio = 0.0

            for n in n_scales:
                # TODO 1: 开启内存追踪与时间记录
                tracemalloc.start()
                start_time = time.perf_counter()
                # TODO 2: 执行函数，传入规模 n
                func(n)
                # TODO 3: 关闭并计算耗时与内存
                end_time = time.perf_counter()
                current, peak_kb = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                cost_ms = end_time - start_time
                # TODO 4: 计算耗时的增长倍率 (当前耗时 / 上一次耗时)
                if prev_time != 0:
                    ratio = cost_ms / prev_time
                else:
                    prev_time = cost_ms
                # 示例输出格式：
                print(
                    f"N={n:<8} | 耗时: {cost_ms:.4f} ms (x{ratio:.2f}) | 内存: {peak_kb:.2f} KB"
                )

        return wrapper

    return decorator


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================


# 我们测试三个数量级：1万、10万、100万
TEST_SCALES = [10_000, 100_000, 1_000_000]


@scaling_benchmark(n_scales=TEST_SCALES)
def naive_list_search(n: int) -> None:
    """【案发现场】在一个大 List 中寻找一个不存在的元素 (触发最坏 O(N))"""
    data_list: List[int] = list(range(n))
    target = -1  # 故意找一个不在里面的数

    # 执行 100 次查询放大常数
    for _ in range(100):
        _ = target in data_list


@scaling_benchmark(n_scales=TEST_SCALES)
def optimized_set_search(n: int) -> None:
    """【防坑策略】在 Set 中寻找同样的元素"""
    # 注意：这里的压测【不包含】数据初始化的时间，只测算高频查询的时间！
    data_set: Set[int] = set(range(n))
    target = -1

    for _ in range(100):
        _ = target in data_set


def test_crucible() -> None:
    print("--- 🚀 开始执行 O(N) 曲线探测 ---")

    print("\n[测试 1] List 线性查询灾难...")
    naive_list_search()

    print("\n[测试 2] Set 常数查询碾压...")
    optimized_set_search()

    print(
        "\n✅ 观察倍率：List 的耗时倍率应该与 N 的倍率（10倍）几乎一致，而 Set 应该始终接近 x1.0！"
    )


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
你的压测器完美揭示了 `list` 随着 N 放大呈现出的线性崩溃，以及 `set` 惊人的 $O(1)$ 稳定性。

但在实际工业现场中，`set` 或 `dict` 的底层是哈希表。
请推演：如果攻击者（或者糟糕的业务数据）故意构造了 10 万个【哈希值完全冲突】的对象存入你的 `dict` 中（即所有数据的 `hash(obj)` 算出来都一样）：
1. 此时你的 `optimized_set_search` 函数，它的时间复杂度会退化成什么？
2. 在这种极端物理条件下，查找耗时会发生什么可怕的灾难？CPython 官方是如何防范这种“哈希碰撞 DDoS 攻击”的？

回答：退化成线性表了，查询效率也是O(N),会检测哈希碰撞，我记得是有一种算法的，我忘记了。
"""
