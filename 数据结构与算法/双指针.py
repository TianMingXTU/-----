# ================= 0. 干活指南与 API 映射 (快思考) ================= #
# 【数据结构与算法】：双指针 (Two Pointers)
#
# 🧠 实用直觉：
# 别管什么时间空间复杂度，你就把它当成一个【游标卡尺】。
# - 场景A【对撞指针】：只要看到“有序数组”、“寻找配对”、“翻转区间”，下意识在两头架设 left 和 right 指针，向中间逼近。
# - 场景B【快慢指针】：只要看到“原地修改数组”、“单向链表找中点/判环”，下意识架设 slow 和 fast 指针。fast 在前面探路，验证合规了，slow 再把数据写进去。
#
# 🛠️ 核心 API 兵器谱：
# 双指针没有花里胡哨的库函数，它考的是你对“索引”或“引用”的掌控力。
# - `left, right = 0, len(arr) - 1`  # 对撞指针初始化
# - `slow, fast = 0, 0`              # 快慢指针初始化

# ================= 1. 环境与依赖准备 ================= #
# 导入今天要干活的核心类型注解
from typing import List

# ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= #


# 【案发现场：干活时的低级错误】
def rookie_mistake(nums: List[int], target_to_remove: int) -> int:
    """
    愚蠢示范：在遍历列表的同时修改列表，或者依赖高成本的 remove 操作。
    在 Python 中，循环内直接调用 .remove() 每次都会触发底层 O(N) 的内存搬运，
    且一边遍历一边删元素，极易导致索引跳跃，漏掉数据！
    """
    for item in nums:
        if item == target_to_remove:
            nums.remove(item)
    return len(nums)


# 【实战干活：TODO】
# 背景说明：接到了一个真实的业务需求。网关层拦截了 100G 的一维访问日志数据块（这里简化为整数数组）。
# 老板要求：把里面状态码为 404 (target) 的脏数据全部剔除。
# 资源限制：服务器内存极其紧张，**绝对禁止**申请新数组（空间复杂度必须 O(1)）。你需要直接在原数组上覆写，并返回清理后有效数据的长度。
# 实战要求：
# 1. 别搞花里胡哨的，用【快慢双指针】把活儿干完。
# 2. 语法必须规范，类型注解写清楚，异常情况（如空数组）必须 Handle。
def pragmatic_in_place_compaction(logs: List[int], target_to_remove: int) -> int:
    """
    原地清理日志数组中的指定脏数据。

    Args:
        logs: 原始日志数组 (会被原地修改)
        target_to_remove: 需要被剔除的脏数据状态码

    Returns:
        清理后有效日志的长度
    """
    # TODO 1: 容错处理：如果日志是空的怎么办？直接返回。
    if not logs:
        return 0

    # TODO 2: 架设快慢双指针。
    # 思考：slow 负责记录什么？fast 负责探路什么？
    slow = 0

    # TODO 3: 开启循环，使用 fast 指针遍历整个日志集。
    # 当 fast 遇到正常日志时，怎么操作？遇到 target_to_remove 脏日志时，怎么操作？
    for fast in range(len(logs)):
        if logs[fast] != target_to_remove:
            logs[slow] = logs[fast]
            slow += 1

    # TODO 4: 返回清洗后的有效日志长度+
    return slow


# ================= 3. 黑盒测试 (Test Cases：交差验收) ================= #
# 模拟 QA 测试你的代码，确保你干的活儿能成功上线。
def test_crucible() -> None:
    test_cases = [
        ([200, 404, 200, 500, 404, 200], 404, 4, [200, 200, 500, 200]),
        ([404, 404, 404], 404, 0, []),
        ([], 404, 0, []),
        ([200, 200], 404, 2, [200, 200]),
    ]

    for i, (logs, target, expected_len, expected_arr) in enumerate(test_cases):
        original_id = id(logs)
        actual_len = pragmatic_in_place_compaction(logs, target)

        # 验证是否就地修改 (未申请新内存)
        assert (
            id(logs) == original_id
        ), f"Case {i}: 内存地址改变，你是不是偷偷 new 了新列表？"
        # 验证返回值
        assert (
            actual_len == expected_len
        ), f"Case {i}: 长度错误，期望 {expected_len}，实际 {actual_len}"
        # 验证数组前部的数据是否正确覆写
        assert (
            logs[:actual_len] == expected_arr
        ), f"Case {i}: 数据覆写错误，期望 {expected_arr}，实际 {logs[:actual_len]}"

    print("✅ QA 测试通过！代码成功合入主分支，准备下班。")


# 当你写完代码后，取消下方注释运行测试：
if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= #
# 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
# 【真实事故场景模拟】：虽然你用双指针搞定了上面的任务，但是业务侧又提了个新需求：“既然能在数组里玩快慢指针，单向链表里的数据去重你肯定也能搞定对吧？”
# 你大手一挥把代码迁移到了链表上。结果上线 3 小时后，服务器 CPU 利用率飙升至 100%，引发全面宕机。
# 运维排查发现，你的指针在一个“带有闭环的脏链表数据”里疯狂空转，陷入了死循环。
#
# 👉 救火任务："别慌，现在让我们看一眼底层概念。在单向链表中，如果数据被意外污染形成了环（Cycle），快慢指针（比如一个走一步，一个走两步）会发生什么神奇的物理现象？为什么一定会发生这个现象？"
