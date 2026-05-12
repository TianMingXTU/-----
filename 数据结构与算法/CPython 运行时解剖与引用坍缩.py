# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【CPython 对象引用模型与状态隔离陷阱】

直觉模型：
在 C++ 里，`int a = 1` 是一块实实在在的 4 字节内存地皮。
但在 Python 里，变量根本不是地皮，而是“便利贴”！`a = 1` 是把写着 'a' 的便利贴，贴在了一个体积庞大的 PyObject 气球上。
当你在列表里装对象时，列表就像一堵墙，上面贴满了指向四面八方的便利贴。

致命陷阱/核心武器：
坑 1：列表乘法陷阱 `[[]] * 3`。你以为造了 3 个气球，其实是 3 张便利贴贴在了同一个气球上。
坑 2：浅拷贝 (Shallow Copy) 陷阱。在使用 LLM Agent 做多路径思考（Tree of Thoughts）时，复制当前状态并往下搜索，结果新分支的修改直接污染了全局老分支。
武器：`copy.deepcopy`（但要小心它的性能黑洞）以及不可变数据结构设计。
"""

# ================= 1. 依赖导入 (Imports) =================
import sys
import copy
from typing import List, Dict, Any

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_agent_state_branching() -> tuple:
    """
    【案发现场】初级工程师：尝试为 Agent 创建一个平行宇宙（新分支）
    """
    # 假设这是 Agent 当前的记忆与状态（包含复杂嵌套）
    base_state: Dict[str, Any] = {
        "step": 1,
        "history": [{"role": "user", "content": "启动 PLC 轮询"}],
        "metadata": {"retry_count": 0},
    }

    # 尝试复制一份状态，用于探索另一条执行路径
    new_branch = base_state.copy()  # 致命一击：浅拷贝

    # 在新分支中修改嵌套数据
    new_branch["history"].append({"role": "assistant", "content": "轮询失败，尝试重置"})
    new_branch["metadata"]["retry_count"] = 1
    new_branch["step"] = 2

    return base_state, new_branch


def robust_agent_state_branching() -> tuple:
    """
    TODO: 在此实现你坚不可摧的状态隔离逻辑
    要求：
    1. 复制 base_state，确保对 new_branch 的任何嵌套修改，绝对不影响 base_state。
    2. 请思考除了直接调用 deepcopy，还有什么更轻量的架构级解法？（提示：写时复制 Copy-on-Write 或 不可变对象）
    """
    base_state: Dict[str, Any] = {
        "step": 1,
        "history": [{"role": "user", "content": "启动 PLC 轮询"}],
        "metadata": {"retry_count": 0},
    }

    # TODO 1: 执行安全的深度隔离复制
    new_branch = copy.deepcopy(base_state)

    # 模拟新分支的业务写入
    new_branch["history"].append({"role": "assistant", "content": "轮询失败，尝试重置"})
    new_branch["metadata"]["retry_count"] = 1
    new_branch["step"] = 2

    return base_state, new_branch


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    print("\n[测试 1] 运行初级代码 (浅拷贝崩溃现场)...")
    base1, branch1 = naive_agent_state_branching()
    print(f"Base State Retry Count: {base1['metadata']['retry_count']} (预期应为 0)")
    print(f"Base State History Length: {len(base1['history'])} (预期应为 1)")

    # 无情 Assert 拦截
    if base1["metadata"]["retry_count"] != 0 or len(base1["history"]) != 1:
        print("❌ 灾难：新分支的修改穿透到了老分支！系统状态被永久污染！")

    print("\n[测试 2] 运行架构师代码 (物理级状态隔离)...")
    base2, branch2 = robust_agent_state_branching()

    if not branch2:  # 如果还没写 TODO，先跳过拦截
        print("⚠️ 检测到 TODO 未完成，等待你的代码。")
        return

    # 严苛的 Assert 拦截
    try:
        assert base2["step"] == 1, "❌ 顶层状态被污染"
        assert base2["metadata"]["retry_count"] == 0, "❌ 嵌套字典状态被污染"
        assert len(base2["history"]) == 1, "❌ 嵌套列表状态被污染"
        print("✅ All Tests Passed! 完美的平行宇宙隔离。")
    except AssertionError as e:
        print(e)

    print("\n[番外篇] CPython 的物理重量")
    print(f"一个空的 Python 列表本身占用内存: {sys.getsizeof([])} Bytes")
    print(
        f"一个基础的 Python 整数占用内存: {sys.getsizeof(1)} Bytes (C语言只要4个字节！)"
    )


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
你现在已经知道用深拷贝（Deepcopy）或者某种手段拦截状态污染了。
但请推演：
如果这是一个高并发的 LLM Agent 流水线，或者是处理海量现场数据的 Adapter，状态树变得极大（比如包含 1000 个元素的历史对话），每走一个分支都 `copy.deepcopy()`。
这会导致什么灾难？
现代工业界（比如不可变数据结构、React 的状态管理、或者底层文件系统的写时复制 COW）是如何在“保证隔离”和“不炸毁内存”之间寻找平衡的？

回答：1、内存爆炸
2、我了解的写时复制的话，只是读取的时候就不会进行复制，是共享的，要是写入的话，就会复制一个新的对象。
"""
