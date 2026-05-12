# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 3.3：文本手术刀 (反向引用 \\1 与 re.sub 的回调管道)】

直觉模型：
- 反向引用 (`\1`, `\2`...)：捕获组不仅能在匹配完成后被取出来，**在正则匹配的过程当中**，它也能被当做条件！
  - 案发现场：你要寻找连续出现的两个一模一样的单词（比如 "the the"）。
  - 直觉写法：`\b(\w+)\s+\1\b`。引擎抓住了第一个单词放进 `(1)` 号瓶里，当游标走到 `\1` 时，它会直接查验瓶子里的内容，要求后面的内容必须跟瓶子里的一模一样。
- `re.sub(pattern, repl, text)` (超级替换引擎)：不仅仅是 `text.replace()` 的平替。
  - 基础玩法：在 `repl` 字符串中，可以直接使用 `\1`, `\g<name>` 把捕获组里的东西按新的格式拼装起来。
  - 高阶神技 (回调函数)：`repl` 可以不是字符串，而是一个**Python 函数**！正则引擎每找到一个匹配，就会把 `Match` 对象扔给这个函数，函数里的 Python 代码想怎么玩就怎么玩，然后返回一个新字符串，引擎负责把它缝合回原处。

致命陷阱/核心武器：
1. 替换灾难：想把 `YYYY-MM-DD` 变成 `DD/MM/YYYY`，如果用普通的 `replace` 或者大量的 `split`，代码会非常臃肿且极易出错。核心武器：`re.sub(r"(\d{4})-(\d{2})-(\d{2})", r"\3/\2/\1", text)`，一行搞定乾坤大挪移。
2. 逻辑死锁：需要把文本中所有的价格（如 "$50"）乘以当时的汇率（1.2）变成 "$60"。正则只负责找文本，它不会算数学题！核心武器：`re.sub` 接收回调函数，在 Python 代码里进行 `float(match.group(1)) * 1.2` 计算。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import Match

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> str:
    """
    【案发现场/初级代码】
    背景：你正在重构一个旧系统的 Markdown 文档。
    任务：把所有的 `[链接文字](http://url)` 格式，强制翻转为 `http://url (链接文字)` 格式。
    """
    # 💣 糟糕的实现：手写大量的字符串切割和查找，一旦遇到多个链接或者格式稍有变化，直接崩溃。
    # 这里就不写了，新手通常会用 while 循环配合 text.find() 痛苦地写 20 行代码。
    pass


def architecture_engine(
    markdown_text: str, current_exchange_rate: float
) -> tuple[str, str]:
    """
    TODO: 在此实现你的高阶架构逻辑
    任务 1 (格式重组)：将所有的 `[文字](URL)` 替换为 `URL (文字)`。
    任务 2 (动态运算)：文本中有一些形如 `$100`, `$5.50` 的美元价格。请利用回调函数，将其全部转换为当前汇率下的价格，保留两位小数，并把 `$` 符号替换为 `¥`。例如汇率是 7.0，`$10` 变成 `¥70.00`。
    """

    # TODO 1: 乾坤大挪移。利用捕获组提取文字和 URL，并在 sub 的第二个参数中用 \1, \2 颠倒它们的位置。
    link_pattern: str = r"\[([^\]]+)\]\(([^)]+)\)"
    replacement_format: str = r"\2 (\1)"  # 例如 r"\2 (\1)"
    new_links_text: str = (
        re.sub(link_pattern, replacement_format, markdown_text)
        if link_pattern
        else markdown_text
    )

    # TODO 2: 动态汇率转换引擎
    price_pattern: str = r"\$([0-9]+\.?[0-9]*)"

    def price_converter(match: Match) -> str:
        # TODO: 提取数字部分，乘以 current_exchange_rate，并格式化为带 ¥ 符号的字符串，保留两位小数。
        # 提示：使用 match.group(1) 拿到数字字符串。

        return f"¥{float(match.group(1)) * current_exchange_rate:.2f}"

    # 利用回调函数进行替换
    new_prices_text: str = re.sub(price_pattern, price_converter, markdown_text)

    return new_links_text, new_prices_text


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    test_text: str = (
        "Please visit [Google](https://google.com) or [GitHub](https://github.com). "
        "The server costs $15.50 per month, and setup fee is $100."
    )
    exchange_rate: float = 7.0

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        links_res, prices_res = architecture_engine(test_text, exchange_rate)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证
    expected_links: str = (
        "Please visit https://google.com (Google) or https://github.com (GitHub). "
        "The server costs $15.50 per month, and setup fee is $100."
    )
    expected_prices: str = (
        "Please visit [Google](https://google.com) or [GitHub](https://github.com). "
        "The server costs ¥108.50 per month, and setup fee is ¥700.00"
    )

    if links_res != expected_links:
        raise AssertionError(
            f"❌ 格式重组失败！\n"
            f"预期: {expected_links}\n"
            f"实际: {links_res}\n"
            f'提示：你的 \1 和 \2 位置放对了吗？防化服 r"" 穿了吗？'
        )

    if prices_res != expected_prices:
        raise AssertionError(
            f"❌ 动态汇率转换失败！\n"
            f"预期: {expected_prices}\n"
            f"实际: {prices_res}\n"
            f"提示：回调函数里正确转换了 float 并且使用了 f-string 格式化两位小数吗？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功握住了数据重组的手术刀。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，我们把一个 Python 函数 `price_converter` 作为参数直接传给了用 C 语言编写的底层正则引擎 `re.sub`。
这种“C 语言调用 Python 函数”的跨语言边界交互，在 Python 解释器中被称为 C-API Callback。

请在脑海中推演：
如果我要清洗一个高达 10GB，包含 1 亿个价格标签的纯文本文件。
1. 使用纯正则替换（如 `re.sub(r"A", "B")`） 和 使用 Python 回调函数替换（如 `re.sub(r"A", py_func)`），在性能和 CPU 开销上会产生多么巨大的物理鸿沟？
2. 导致这种物理鸿沟的根本原因是什么？（提示：思考 GIL 锁、Python 对象的创建销毁开销、以及 C 与 Python 环境之间的上下文切换）。

回答：re.sub(r"A", py_func)会导致程序在等待py_func完成，Python是脚本语言，运行的很慢。
"""
