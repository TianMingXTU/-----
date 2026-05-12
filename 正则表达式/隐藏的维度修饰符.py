# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 2.3：隐藏的维度修饰符 (忽略大小写 re.I、多行模式 re.M、单行穿透 re.S)】

直觉模型：
正则表达式有几个极其强大的隐藏开关（Flags），可以通过 `flags=...` 参数传入：
- `re.I` (IGNORECASE，忽略大小写)：给游标戴上色盲眼镜。`a` 和 `A` 在它眼里不再有区别。
- `re.M` (MULTILINE，多行模式)：打破 `^` 和 `$` 的单行诅咒。默认情况下，`^` 只匹配整个超长字符串的最开头。开启 `re.M` 后，字符串里的每一个换行符 `\\n` 之后，都会诞生一个新的 `^`；每一个 `\\n` 之前，都会诞生一个新的 `$`。
- `re.S` (DOTALL，单行穿透)：赋予通配符 `.` 真正的神力。默认情况下，`.` 可以匹配宇宙中的任何字符，**唯独不能匹配换行符 `\\n`**。开启 `re.S` 后，`.` 将贯穿换行符，视多行文本为一整块无缝的钢铁。

致命陷阱/核心武器：
1. 组合开关：很多时候我们需要同时开启多个维度，比如既要忽略大小写，又要多行匹配。核心武器：使用按位或运算符 `|` 组合，例如 `flags=re.I | re.M`。
2. 跨行提取的痛点：提取被 `<config>...</config>` 包裹的数十行配置信息，如果不用 `re.S`，`.` 走到第一行末尾就撞墙死了。核心武器：`re.S` 配合非贪婪量词 `.*?`，完美剥离跨行块。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> Tuple[List[str], List[str]]:
    """
    【案发现场/初级代码】
    背景：你要解析一份极其混乱的系统崩溃日志。
    任务 1：提取所有真正以 "error:" 开头（必须在行首，且大小写不管）的报错原因。
    任务 2：提取被 <dump> 和 </dump> 包裹的完整多行内存快照。
    """
    # 💣 致命错误 1：没有加 re.I，漏掉了 "ERROR:"；没有加 re.M，导致 ^ 只认第一行。
    error_pattern: str = r"^error:\s*(.*)"
    reasons: List[str] = re.findall(error_pattern, text)

    # 💣 致命错误 2：没有加 re.S，导致 .* 遇到换行符直接停止匹配，什么都提不出来。
    dump_pattern: str = r"<dump>(.*?)</dump>"
    dumps: List[str] = re.findall(dump_pattern, text)

    return reasons, dumps


def architecture_engine(text: str) -> Tuple[List[str], List[str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 提取出所有在【每一行行首】出现的错误原因（去掉 "error:" 本身，只留后面的内容）。"Error:", "ERROR:", "eRrOr:" 都算。
    2. 提取出 `<dump>` 和 `</dump>` 标签之间的完整多行文本。
    """
    error_pattern: str = r"^error:\s*(.*)"
    # TODO 1: 传入正确的 flags 组合（提示：利用 | 运算符组合多个修饰符）
    reasons: List[str] = (
        re.findall(error_pattern, text, flags=re.I | re.M) if error_pattern else []
    )

    dump_pattern: str = r"<dump>(.*?)</dump>"
    # TODO 2: 传入正确的 flag，让 . 能够贯穿 \n
    dumps: List[str] = (
        re.findall(dump_pattern, text, flags=re.S) if dump_pattern else []
    )

    return reasons, dumps


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    crash_log: str = (
        "System Booting...\n"
        "ERROR: core dumped\n"  # 应该被提取: core dumped
        "warning: disk space low\n"
        "Some text with error: fake\n"  # 不应该提取，因为它不在行首！
        "eRRoR:   memory leak\n"  # 应该被提取: memory leak (注意可能有多余的空格)
        "<dump>\n"
        "0x0001: FF AA\n"
        "0x0002: BB CC\n"
        "</dump>\n"
        "End of log."
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        reasons, dumps = architecture_engine(crash_log)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证
    expected_reasons: List[str] = ["core dumped", "memory leak"]
    expected_dumps: List[str] = ["\n0x0001: FF AA\n0x0002: BB CC\n"]

    if reasons != expected_reasons:
        raise AssertionError(
            f"❌ 报错原因提取失败！\n"
            f"预期: {expected_reasons}\n"
            f"实际: {reasons}\n"
            f"提示：^ 真的卡住了每一行的开头吗？re.I 和 re.M 组合正确吗？空格处理对了吗？"
        )

    if dumps != expected_dumps:
        raise AssertionError(
            f"❌ 内存快照提取失败！\n"
            f"预期: {expected_dumps}\n"
            f"实际: {dumps}\n"
            f"提示：你的游标是不是遇到第一行的 \\n 就停滞不前了？穿甲弹 (re.S) 装填了吗？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功获得了多维度的提取能力。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，我们利用 `re.S` 让 `.*` 能够跨越多行提取日志。
假设你现在要处理一个高达 1GB 的 XML 文件，你需要提取其中的某个 `<node>.*?</node>`。

请在脑海中推演：
如果你在开启了 `re.S` (DOTALL) 的同时，**不小心忘记了**写非贪婪的 `?`，直接写成了 `<node>.*</node>`。
相比于没有开启 `re.S` 时忘记写 `?`，开启了 `re.S` 后的贪婪模式，会在内存和回溯引擎中引发什么极其恐怖的物理灾难？
提示：思考一下不带 `re.S` 时，贪婪的推土机最远能推到哪里？带了 `re.S` 后，它又能推到哪里？

回答：1、非贪婪的话，那么将会在内存里面匹配高达 1GB 的 XML 文件，也即是类似于完全加载。
"""
