# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 4.3：可维护性与测试防线 (re.compile 与 re.VERBOSE / re.X)】

直觉模型：
- `re.compile` (锻造台)：正则字符串（如 `r"\d+"`）本身只是纯文本。每次调用 `re.match` 时，底层 C 引擎都需要先把它“编译”成状态机（NFA/DFA）。如果在千万级的循环里不断调用 `re.match`，其实是在反复编译。核心武器：在循环外部，用 `pattern_obj = re.compile(r"...")` 提前锻造好状态机，在循环内直接调用 `pattern_obj.search(text)`，榨取极致性能。
- `re.VERBOSE` / `re.X` (结构化透视镜)：默认情况下，正则里的空格就是物理空格。一旦开启 `re.X` 修饰符，正则引擎会**彻底忽略模式字符串中的所有空白字符（空格、换行、制表符）**，并且**允许使用 `#` 添加注释**！这就允许我们把一行“天书”，拆解成多行带有详细注释的工业级配置文件。

致命陷阱/核心武器：
1. 物理空格的误杀：开启了 `re.X` 后，你正则里的空格都会被忽略。如果你真的需要匹配物理世界的空格怎么办？核心武器：必须显式地写 `\s`，或者把空格用防化服转义 `\ `。
2. 团队协作的崩溃：在接手旧项目时，看到 `r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"` 这种强校验 IP 的正则，没人敢去改里面的任何一个符号。核心武器：彻底重写为多行 `re.VERBOSE` 格式，打上详细注释，留给后人一条活路。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Dict

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(log_lines: List[str]) -> List[Dict[str, str]]:
    """
    【案发现场/初级代码】
    背景：你正在监控一个名为 Nexus 的分布式任务调度系统。
    你需要从海量的节点心跳日志中提取：时间戳、节点ID、任务哈希、执行状态、负载指标。
    """
    results = []
    # 💣 致命错误 1：极其冗长、不可读的“天书”正则，连命名分组都挤在一行，谁看谁崩溃。
    # 💣 致命错误 2：在千万级的 for 循环内部直接使用 re.search 纯文本，每次都在做无谓的 C 层级重新编译。
    ugly_pattern = r"\[(?P<time>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s+\[(?P<node>NEXUS-NODE-\d+)\]\s+TASK_ID:\s+(?P<task>[a-f0-9]+)\s+STATUS:\s+(?P<status>[A-Z]+)\s+METRIC:\s+(?P<metric>[0-9.]+)"

    for line in log_lines:
        match = re.search(ugly_pattern, line)
        if match:
            results.append(match.groupdict())

    return results


def architecture_engine(log_lines: List[str]) -> List[Dict[str, str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 使用多行字符串 `r\"\"\" ... \"\"\"` 配合 `re.X`（即 `re.VERBOSE`），把上面的 `ugly_pattern` 彻底拆解。
    2. 为每一行正则片段加上 `#` 注释，解释它在提取什么。
    3. 注意：开启 re.X 后，原日志中用来分隔字段的物理空格会失效，你需要用 `\s+` 来严谨占位。
    4. 将正则“提前编译”为一个对象，然后在循环内部使用该对象的 `.search()` 方法。
    """

    # TODO 1: 编写多行、带注释的优雅正则
    elegant_pattern_str = r"""
    # =========================
    # 时间戳
    # [2025-05-12 10:22:11]
    # =========================
    \[
        (?P<time>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})
    \]

    \s+

    # =========================
    # 节点ID
    # [NEXUS-NODE-7]
    # =========================
    \[
        (?P<node>NEXUS-NODE-\d+)
    \]

    \s+

    # =========================
    # TASK_ID
    # TASK_ID: a3f91c2d
    # =========================
    TASK_ID:

    \s+

    (?P<task>[a-f0-9]+)

    \s+

    # =========================
    # STATUS
    # STATUS: SUCCESS
    # =========================
    STATUS:

    \s+

    (?P<status>[A-Z]+)

    \s+

    # =========================
    # METRIC
    # METRIC: 98.75
    # =========================
    METRIC:

    \s+

    (?P<metric>[0-9.]+)
"""

    # TODO 2: 在循环外部，提前编译好状态机 (别忘了传入 re.X 修饰符)
    compiled_engine = re.compile(elegant_pattern_str, re.VERBOSE | re.X)

    results: List[Dict[str, str]] = []

    for line in log_lines:
        # TODO 3: 调用编译好的引擎对象进行搜索
        match = compiled_engine.search(line)
        if match:
            results.append(match.groupdict())

    return results


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    nexus_logs: List[str] = [
        "[2026-05-11 10:00:00] [NEXUS-NODE-01] TASK_ID: 9a4b STATUS: RUNNING METRIC: 0.99",
        "Some corrupted log line without proper format...",
        "[2026-05-11 10:05:12] [NEXUS-NODE-04] TASK_ID: f7c2 STATUS: FAILED METRIC: 1.05",
    ]

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        results = architecture_engine(nexus_logs)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证
    expected_results: List[Dict[str, str]] = [
        {
            "time": "2026-05-11 10:00:00",
            "node": "NEXUS-NODE-01",
            "task": "9a4b",
            "status": "RUNNING",
            "metric": "0.99",
        },
        {
            "time": "2026-05-11 10:05:12",
            "node": "NEXUS-NODE-04",
            "task": "f7c2",
            "status": "FAILED",
            "metric": "1.05",
        },
    ]

    if results != expected_results:
        raise AssertionError(
            f"❌ 结构化解析失败！\n"
            f"预期: {expected_results}\n"
            f"实际: {results}\n"
            f"提示：使用 re.X 后，你是不是漏写了物理边界占位的 `\s+`？括号和命名提取的语法完整吗？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功锻造了可维护的工业级代码。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，我们强制要求你使用 `re.compile()` 在循环外部提前编译。
但如果你翻阅 Python `re` 模块的底层 C 源码，你会发现：即使你直接在循环里写 `re.search(pattern, text)`，Python 其实在底层隐式地维护了一个缓存字典（默认为 `_MAXCACHE = 512`），它会悄悄把你最近用过的纯文本正则编译好并缓存起来。

既然 Python 底层已经有自动缓存了，为什么在工业界的代码规范（如 Google Python Style Guide 或你的项目架构标准）中，依然**强烈建议/强制要求**在处理海量循环时，显式地在外部使用 `re.compile()` 进行预编译？
提示：思考函数调用的压栈开销、字典的 Hash 查找成本、以及当项目极其庞大时缓存池被击穿（Cache Eviction）的风险。

回答：我虽然不知道原理，但是我认为主要是怕编译后的结果太长了，_MAXCACHE = 512不够。而且函数
他是放在栈帧里面的，每一次调用都属于要在栈里面进行计算，在字典里面查找的话也会有哈希冲突吧。
"""
