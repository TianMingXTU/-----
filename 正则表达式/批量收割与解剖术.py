# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 2.2：批量收割与解剖术 (re.finditer 与 Match 对象)】

直觉模型：
- `re.findall` (暴力收割机)：直接把所有匹配到的字符串塞进一个大列表里扔给你。简单粗暴，但它丢失了“作案现场”的位置信息。
- `re.finditer` (流式法医探照灯)：它不返回字符串，而是返回一个**迭代器 (Iterator)**。每次迭代，它都会交给你一个 `Match` 对象。
- `Match` 对象 (法医检验报告)：它包含了游标扫过这片区域时的所有物理状态。
  - `match.group()`：提取出真正匹配到的字符串本身（收缴的赃物）。
  - `match.span()`：返回一个元组 `(start, end)`，精确告诉你这个字符串在原始文本中的物理索引范围（作案的 GPS 坐标）。

致命陷阱/核心武器：
1. OOM 灾难：当你在几十 GB 的日志文本中提取上亿个 Token 时，`findall` 会在内存中瞬间生成一个包含上亿个字符串的超级大列表，直接把机器内存撑爆 (OOM)。核心武器：`finditer` 是惰性求值 (Lazy Evaluation) 的，每次只在内存中生成当前的那一个 Match 对象。
2. 上下文丢失与替换灾难：很多时候你需要把脏词替换掉，或者提取脏词前后 5 个字符作为上下文交给 LLM。`findall` 拿出来的只是词本身，你根本不知道它原来在文本的哪个角落。核心武器：用 `match.span()` 获取绝对坐标，然后通过切片 `text[start-5:end+5]` 精准提取上下文。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple, Iterator

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str, pattern: str) -> List[str]:
    """
    【案发现场/初级代码】
    背景：老板让你在一篇极其漫长的内部审查文档中，找出所有被标记为 [CONFIDENTIAL] 的敏感词。
    并且要求你将其高亮，或者提取出敏感词前后的上下文。
    """
    # 💣 致命错误：findall 只返回了字符串列表，完全丢失了物理坐标。老板问你这些词在文档的第几行第几个字，你当场傻眼。
    matches: List[str] = re.findall(pattern, text)
    return matches


def architecture_engine(text: str, pattern: str) -> List[Tuple[str, int, int]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    使用流式提取器，扫描整个文本，找到所有匹配 pattern 的内容。
    将结果组装成一个列表返回，列表中的每个元素必须是一个元组：
    (匹配到的字符串, 开始索引, 结束索引)
    """
    results: List[Tuple[str, int, int]] = []

    # TODO 1: 放弃 findall，使用 re.finditer 获取一个包含 Match 对象的迭代器
    matches = re.finditer(pattern, text)
    # TODO 2: 遍历这个迭代器，利用 Match 对象的 .group() 和 .span() 方法，提取出需要的数据，并塞入 results
    for match in matches:
        string = match.group()
        index = match.span()
        results.append((string, *index))

    return results


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    document: str = (
        "The launch code is [CONFIDENTIAL]. Do not share it. "
        "Also, the server IP [CONFIDENTIAL] must be hidden."
    )
    secret_pattern: str = r"\[CONFIDENTIAL\]"

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        results = architecture_engine(document, secret_pattern)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_results: List[Tuple[str, int, int]] = [
        ("[CONFIDENTIAL]", 19, 33),
        ("[CONFIDENTIAL]", 72, 86),
    ]

    if results != expected_results:
        raise AssertionError(
            f"❌ 坐标提取失败！\n"
            f"预期: {expected_results}\n"
            f"实际: {results}\n"
            f"提示：你是不是没有正确调用 Match 对象的 .span() 或没解包其返回值？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功掌握了流式法医探照灯。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
代码跑通只是及格。
请在脑海中推演：假设我要处理的 `document` 不是短短两行，而是一个高达 50GB 的 Nginx 访问日志文件。我要提取出里面所有的恶意 SQL 注入载荷（数量可能高达数千万个）。

1. 如果你坚持使用 `re.findall`，在 Python 底层的内存中会发生怎样恐怖的连环爆炸？（请结合 Python 列表底层的动态扩容机制来思考）。
2. 为什么 `re.finditer` 配合上游的流式读取，能在处理这 50GB 日志时，将内存占用稳定保持在极低的水平？它是如何与 Python 的 `yield` (生成器) 机制在物理层面配合的？

回答：1、内存爆炸，而且进行反复的拷贝，浪费时间
2、惰性求值，每一次返回一个match对象,可以写一个函数，在循环里面使用yield进行返回，构建一个生成器函数。
"""
