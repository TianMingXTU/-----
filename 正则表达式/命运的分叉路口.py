# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 3.1：命运的分叉路口 (分支选择 | 及其隐患)】

直觉模型：
- `|` (逻辑 OR)：把正则变成了两条岔路。游标走到这里时，如果左边的路不通，它会自动回退并尝试走右边的路。例如 `cat|dog`，要么吃掉猫，要么吃掉狗。

致命陷阱/核心武器：
1. 短路陷阱 (Short-circuiting)：正则引擎的 `|` 极其“功利”。它总是**从左到右尝试**，一旦左边的分支匹配成功，它立刻拿着战利品跑路，看都不看右边一眼！
   - 案发现场：尝试用 `python|python3` 匹配字符串 "I use python3"。
   - 惨剧：游标发现第一条路 `python` 完美匹配了前面的字符，直接停机，只提取出了 "python"，丢掉了后面的 "3"！
   - 核心武器：在构建包含公共前缀的分支时，**务必将最长的分支写在最左边**，例如 `python3|python`。
2. 作用域灾难：当你写下 `I love cat|dog` 时，你以为是“我爱猫或狗”，但引擎理解的是：“要么是『I love cat』，要么是孤零零的一个『dog』”。
   - 核心武器：用括号 `()` 画定逻辑的势力范围：`I love (cat|dog)`。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> List[str]:
    """
    【案发现场/初级代码】
    背景：你需要从简历中精准提取应聘者的职位意向。
    目标职位包括三种："软件工程师", "高级软件工程师", "架构师"。
    你还需要匹配出求职者所掌握的关键语言。
    """
    # 💣 致命错误 1：短路陷阱。由于"软件工程师"写在前面，"高级软件工程师"永远不会被完整匹配出来，高级全变初级。
    title_pattern: str = r"软件工程师|高级软件工程师|架构师"
    titles: List[str] = re.findall(title_pattern, text)

    # 💣 致命错误 2：作用域灾难。没有加括号，引擎理解为“前面的内容”或者“后面的内容”。
    lang_pattern: str = r"I master Python|Java|Go"
    langs: List[str] = re.findall(lang_pattern, text)

    return titles, langs


def architecture_engine(text: str) -> List[str]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 完美提取出文本中所有出现的职位名称："软件工程师", "高级软件工程师", "架构师"。
    2. 完美提取出特定的短语句式："I master " 加上具体的语言名（包含：Python, Java, Go, C++）。
       最终提取的结果必须是完整的句子，比如 "I master C++"。
    """

    # TODO 1: 避开短路陷阱，重排分支顺序，写出无损提取职位的 title_pattern
    title_pattern: str = r"高级软件工程师|软件工程师|架构师"

    # TODO 2: 用括号圈定分支的势力范围，写出完整的 lang_pattern。
    # ⚠️ 极度危险提示：Python re.findall 的隐藏诅咒！
    # 如果你的正则里有捕获组 `()`，findall 会自作聪明地**只返回组里的内容**，丢弃外面的字符。
    # 如何在圈定作用域的同时，让括号丧失“记忆/捕获”功能，从而返回整个句子？
    # 翻阅前置地图（非捕获组），或者用你的快思考盲猜一下那个由 ?: 组成的魔法符号。
    lang_pattern: str = r"I master (?:Python|Java|Go|C\+\+)"

    titles: List[str] = re.findall(title_pattern, text) if title_pattern else []
    langs: List[str] = re.findall(lang_pattern, text) if lang_pattern else []

    return titles + langs  # 为了方便测试，合并输出


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    resume_text: str = (
        "Hello, I am aiming for 高级软件工程师. If not, 软件工程师 is fine. "
        "I also admire the 架构师 role. "
        "As for skills, I master Python and I master Go. "
        "Java is good, but I master C++ mostly. I master Rust is not targeted."
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        results = architecture_engine(resume_text)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_results: List[str] = [
        "高级软件工程师",
        "软件工程师",
        "架构师",
        "I master Python",
        "I master Go",
        "I master C++",
    ]

    if results != expected_results:
        raise AssertionError(
            f"❌ 提取发生灾难性碎裂！\n"
            f"预期: {expected_results}\n"
            f"实际: {results}\n"
            f"提示：'高级软件工程师' 是不是被短路截断成'软件工程师'了？或者 findall 因为括号的诅咒只吐出了 'Python' 而不是完整的句子？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功跨越了命运的分叉口。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，为了对抗 `findall` 遇到 `()` 就只返回局部内容的潜规则，我们使用了非捕获组 `(?:...)`。
在很多业务代码里，初级工程师非常喜欢到处写大量的普通括号 `()`，哪怕他们根本不需要提取这部分内容，仅仅是为了把几个字符绑在一起加个 `*` 或者 `|`。

请在脑海中推演，如果你在一个长达千行的正则表达式中，随意滥用了 50 个普通捕获组 `()`：
1. 引擎在执行物理匹配时，为了记录这些普通捕获组，底层内存和寄存器会付出什么隐性代价？
2. 在大规模高并发请求下，为什么要将纯粹用于逻辑分组的 `()` 严格替换为 `(?:...)`？

回答：1、底层内存和寄存器应该进行匹配和交互，浪费性能，他会捕获结果啊
2、因为(?:...)性能更好，只分组，不捕获结果
"""
