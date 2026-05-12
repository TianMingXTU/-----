# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【工业基准压测与 CPython 性能黑洞】

直觉模型：
把时间复杂度看作“服务器账单”，空间复杂度看作“仓库租金”。
O(1) 是一次性买断；O(N) 是按件计费；O(N^2) 是高利贷，业务量翻倍，账单直接原地爆炸。
但要注意：Python 的 1 个整数并不是 C 语言里的 4 个字节，而是一个庞大的 PyObject 结构体。这就是为什么 Python 常数极高的物理原因。

致命陷阱/核心武器：
坑 1：用 `time.time()` 测算性能（精度极差且受系统时钟回拨影响）。武器：`time.perf_counter`。
坑 2：以为变量被 del 掉内存就释放了。武器：`tracemalloc` 追踪真实的内存分配峰值。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import tracemalloc
from functools import wraps
from typing import Callable, Any, List
from collections import deque

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def benchmark_harness(func: Callable) -> Callable:
    """
    TODO: 在此实现你的工业级压测装饰器
    要求：
    1. 耗时测算：使用高精度时钟，计算精确耗时（毫秒级）。
    2. 内存测算：使用 tracemalloc 记录函数执行期的【内存增量峰值】（KB 级）。
    3. 拦截与透传：必须完美返回原函数的返回值，不能破坏原函数的签名。

    Returns:
        Callable: 包装后的函数
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # TODO 1: 启动 tracemalloc 并记录开始时间
        tracemalloc.start()
        start_time = time.perf_counter()

        # TODO 2: 执行原函数获取结果
        result = func(*args, **kwargs)

        # TODO 3: 记录结束时间，获取内存快照，并计算耗时与内存增量
        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # TODO 4: 格式化打印压测报告：[函数名] 耗时: xxx ms | 内存峰值: xxx KB
        print(
            f"[{func.__name__}] 耗时: {end_time-start_time} | 内存峰值: {peak/1024:.2f}KB"
        )

        return result

    return wrapper


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================


@benchmark_harness
def naive_list_insert(n: int) -> List[int]:
    """【案发现场】初级工程师：在列表头部疯狂插入数据"""
    arr: List[int] = []
    for i in range(n):
        arr.insert(0, i)  # 致命：每次插入导致整个数组内存平移
    return arr


@benchmark_harness
def optimized_deque_insert(n: int) -> deque:
    """【防坑策略】架构师：使用双端队列处理头部高频操作"""
    arr: deque = deque()
    for i in range(n):
        arr.appendleft(i)  # 优雅：双向链表块级分配，O(1) 插入
    return arr


def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")
    N = 100_000  # 十万次数据写入

    print("\n[测试 1] 运行初级代码 (List Insert 0)... 请耐心等待，它会很慢！")
    naive_list_insert(N)

    print("\n[测试 2] 运行架构师代码 (Deque Appendleft)...")
    optimized_deque_insert(N)

    print("\n✅ 压测脚手架执行完毕。对比两次输出的耗时差异！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
你的 Benchmark Harness 应该已经清楚地展示了 `list.insert(0)` 和 `deque.appendleft` 在耗时上的巨大鸿沟（可能是成百上千倍的差距）。

请在脑海中推演并回答：
1. 从底层 C 语言数组内存布局的角度，解释为什么 `list.insert(0)` 在数据量变大时，耗时会呈指数级崩溃（O(N^2) 陷阱）？物理上到底发生了什么动作？
2. 在 Python 中，当我们往 `list` 里 `append` 10万个整数时，列表分配的内存大小，是严格等于 10万 * sizeof(int) 吗？如果不是，CPython 底层使用了什么机制来避免频繁的系统调用（syscall）申请内存？

回答：1、因为每一次插入就要移动N个元素，如果插入N个，那样时间复杂度就是O(N^2)，而且C语言数组的内存空间大小是固定的，超过了的话，就要去申请更多的内存，并且将原来内存的内容拷贝到新的数组里面，这样的话，原来的缓存也失效了，得从新构建。
2、不会，应该是大于10万* sizeof(int)，因为list里面的元素是一个对象，这个对象，包括变量、引用计数的部分、地址部分，类型部分，所以就会很大。而且申请的内存的时候不会是每一次都要申请，而且一次性就申请到扩大一倍的内存。
"""
