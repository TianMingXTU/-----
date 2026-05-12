# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 1.2：贪婪与懒惰的边界 (量词与非贪婪模式的游标推进逻辑)】

直觉模型：
我们要控制吃豆人 (游标) 吃东西的“胃口”。
- 量词 (`*`, `+`, `?`, `{m,n}`)：定义了吃的数量。
  - `*`：0 次或多次（可以不吃）。
  - `+`：1 次或多次（至少吃一口）。
  - `?`：0 次或 1 次（吃或不吃，绝不多吃）。
- 贪婪模式 (Greedy, 默认行为)：像一台**推土机**。遇到 `.*` 时，它会一口气把整行文本推到尽头，然后再因为后面的条件不匹配，一点点把吃进去的字符“吐出来”（这叫回溯 Backtracking），直到整体匹配成功。
- 懒惰/非贪婪模式 (Lazy, 在量词后加 `?`，如 `.*?`)：像一个**极其谨慎的试探者**。它每次只往前走一小步（吃一个字符），然后立刻抬头看后面的条件满足了没有。一旦满足，它立刻停嘴，绝不多吃。

致命陷阱/核心武器：
1. HTML/XML 标签的吞噬灾难：用 `<.*>` 去匹配 `<thought>...</thought>`，推土机会直接从第一个 `<` 一口吞到整段文本最后一个 `>`，把中间所有标签全吃了。核心武器：非贪婪模式 `<.*?>`。
2. 懒惰的性能代价：虽然 `.*?` 能精确卡住边界，但它每走一步都要停下来判断，在长文本中可能引发频繁的上下文切换。真正的大神在某些场景下，会用“严格的排除字符类” `[^>]*` 来替代 `.*?`，既快又准。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> Tuple[List[str], List[str]]:
    """
    【案发现场/初级代码】
    背景：你正在开发一个 LLM Agent 监控系统，需要从模型输出的冗长日志中，
    精准提取出它的内部思考过程（包裹在 <thought> 和 </thought> 之间），
    以及模型调用的外部工具命令（使用双引号 "..." 包裹）。
    """
    # 💣 致命错误 1：默认贪婪，导致跨越多个标签，把中间的非 thought 文本也吞了
    # 💣 致命错误 2：双引号匹配同样默认贪婪，把两个独立的命令连同中间的废话一起吞了
    thought_pattern: str = r"<thought>.*</thought>"
    command_pattern: str = r'".*"'

    thoughts: List[str] = re.findall(thought_pattern, text)
    commands: List[str] = re.findall(command_pattern, text)
    return thoughts, commands


def architecture_engine(text: str) -> Tuple[List[str], List[str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 提取出每一个独立的 `<thought>` 标签对内部的完整内容（需要包含标签本身）。如果有多个，必须分别独立提取，不能合并。
    2. 提取出被双引号 `"` 包裹的完整字符串命令（需包含双引号本身）。同样，必须独立提取。
    """
    # TODO 1: 降伏贪婪的推土机，写出能精准停留在最近一个闭合标签的 thought_pattern
    thought_pattern: str = r"<thought>.*?\</thought>"

    # TODO 2: 思考除了 .*? 之外，是否能用“字符类取反”的思想，写出更高效、更具物理防御力的 command_pattern？
    command_pattern: str = r"\"[^\"]*\""

    thoughts: List[str] = re.findall(thought_pattern, text) if thought_pattern else []
    commands: List[str] = re.findall(command_pattern, text) if command_pattern else []

    return thoughts, commands


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    # 模拟一段 LLM Agent 的复杂输出日志
    agent_log: str = (
        "Agent Starting... <thought>I need to search the database first.</thought> "
        'Then I will execute "SELECT * FROM users". '
        "Wait, <thought>Maybe I should check the cache?</thought> "
        'Executing "redis-cli ping" instead.'
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        thoughts, commands = architecture_engine(agent_log)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_thoughts: List[str] = [
        "<thought>I need to search the database first.</thought>",
        "<thought>Maybe I should check the cache?</thought>",
    ]
    expected_commands: List[str] = ['"SELECT * FROM users"', '"redis-cli ping"']

    if thoughts != expected_thoughts:
        raise AssertionError(
            f"❌ 思考过程提取失败！\n预期: {expected_thoughts}\n实际: {thoughts}\n提示：推土机是不是直接从第一个 <thought> 推到了最后一个 </thought>？"
        )

    if commands != expected_commands:
        raise AssertionError(
            f"❌ 命令提取失败！\n预期: {expected_commands}\n实际: {commands}\n提示：你的游标是不是在两个命令之间一路狂奔，把不该吃的东西全吃进去了？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功驯服了贪婪的游标。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，提取双引号字符串，很多人会下意识地写 `".*?"`。
但请你在脑海中推演：如果这个 Agent 输出了一个长达 1MB 的无格式纯文本（没有双引号），游标使用 `".*?"` 会如何移动？
对比使用 `"[^"]*"` （匹配一个引号，接着是任意数量的“非引号”字符，最后是闭合引号），在底层执行路径和性能表现上会有什么本质差异？

回答：1、".*?"会逐个移动，并且每一次移动后都要判断是不是到达了终点。"[^"]*不需要判断，但是需要回溯，总体而言"[^"]*的性能更好好。
"""
