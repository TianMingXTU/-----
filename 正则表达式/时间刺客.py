# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 4.1：时间刺客 / 零宽断言 (Lookahead & Lookbehind)】

直觉模型：
把正常的正则匹配比作“吃豆人”吃掉赛道上的豆子，游标会随着吃豆向前移动。
而“零宽断言（环视）”是吃豆人派出的“幽灵侦察兵”。幽灵可以往左看（过去），也可以往右看（未来），确认条件是否满足。但幽灵没有任何物理实体（零宽度），它看完之后就会消失，**游标的位置不会有哪怕 1 毫米的移动，字符也不会被吃掉**。

- `(?=...)` 正向先行断言 (Lookahead)：向右看未来。`\d+(?= USD)` 意思是“找到数字，且它的右边必须是 USD”。提取结果只有数字，没有 USD。
- `(?!...)` 负向先行断言 (Negative Lookahead)：向右看未来，确保**不是**某个东西。
- `(?<=...)` 正向后顾断言 (Lookbehind)：向左看过去。`(?<=￥)\d+` 意思是“找到数字，且它的左边必须是￥”。
- `(?<!...)` 负向后顾断言 (Negative Lookbehind)：向左看过去，确保**不是**某个东西。

致命陷阱/核心武器：
1. Python 的绝对禁忌：Python 内置的 `re` 模块，其底层的 C 引擎在处理“后顾断言（向左看）”时，有一个极其严苛的物理限制——**后顾断言必须是固定长度 (Fixed-width)！**
   - 案发现场：`(?<=a|bc)` 是非法的，因为 `a` 长度是 1，`bc` 长度是 2。`(?<=a.*b)` 更是绝对非法的，因为它长度不可预知。一旦运行，直接抛出 `re.error: look-behind requires fixed-width pattern` 异常。
   - 破局武器：面对变长的前缀条件，顶级工程师通常会放弃后顾断言，转而利用上一节学过的“普通捕获组 `()`”来精准拿捏：把前置条件用 `(?:...)` 匹配掉（消耗掉），真正想要的数据用 `()` 捕获。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> Tuple[List[str], List[str]]:
    """
    【案发现场/初级代码】
    背景：你需要从混杂的财务与代码日志中，精准提取特定数据。
    任务 1：提取所有面额是 "USD" 的金额数字（但不提取 USD 字母本身）。
    任务 2：提取版本号数字。前提是它的前面必须是 "v" 或者 "version "（长度分别是 1 和 8）。
    """
    # 💣 致命错误 1：没有使用零宽断言，把后面的 USD 也吃进去了。
    usd_pattern: str = r"\d+\s*USD"
    usds: List[str] = re.findall(usd_pattern, text)

    # 💣 致命错误 2：Python 严禁在后顾断言里使用变长字符（v 长度1，version 长度8）。
    # 如果你解除下面这行代码的注释，程序会当场抛出编译异常引擎崩溃！
    # version_pattern: str = r"(?<=v|version )\d+\.\d+"
    # versions: List[str] = re.findall(version_pattern, text)

    return usds, []


def architecture_engine(text: str) -> Tuple[List[str], List[str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 使用“正向先行断言（向右看）”，提取出纯数字，条件是其右侧跟着 " USD"（可能有空格，也可能没有，如 "100USD" 或 "200 USD"）。不要把 USD 提取出来！
    2. 面对变长的左侧条件（"v" 或 "version "），你需要绕过 Python `re` 模块后顾变长的报错死穴。
       提示：不要头铁去写非法的后顾断言了！利用普通的正则匹配掉前缀，然后把想要提取的版本号用 `()` 圈起来。还记得 re.findall 遇到 `()` 会发生什么奇妙的化学反应吗？
    """

    # TODO 1: 派出向右看的刺客。注意 USD 前面可能存在的变长空格 \s*。
    # 既然是向右看，Python 是允许变长的。
    usd_pattern: str = r"\d+(?=\s*USD)"

    # TODO 2: 降维打击。放弃向左看的刺客，改用“非捕获组匹配前缀” + “捕获组提取核心数据”的组合拳。
    version_pattern: str = r"(?:v|version )(\d+\.\d+)"

    usds: List[str] = re.findall(usd_pattern, text) if usd_pattern else []
    versions: List[str] = re.findall(version_pattern, text) if version_pattern else []

    return usds, versions


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    log_data: str = (
        "Server costs 100USD, refund 50 EUR. Additional charge is 200    USD. "
        "System updated to v1.2. Old version is version 0.9. Ignore v_error2.0."
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        usds, versions = architecture_engine(log_data)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_usds: List[str] = ["100", "200"]
    expected_versions: List[str] = ["1.2", "0.9"]

    if usds != expected_usds:
        raise AssertionError(
            f"❌ USD 金额提取失败！\n"
            f"预期: {expected_usds}\n"
            f"实际: {usds}\n"
            f"提示：你的刺客是不是没看清右侧？或者不小心把 USD 也吃进去了？"
        )

    if versions != expected_versions:
        raise AssertionError(
            f"❌ 版本号提取失败！\n"
            f"预期: {expected_versions}\n"
            f"实际: {versions}\n"
            f"提示：你绕开后顾变长的死穴了吗？前缀条件匹配对了吗？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print(
        "✅ All Tests Passed! 恭喜 AC！你成功驾驭了时间刺客，并绕过了 Python 的底层结界。"
    )


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的 TODO 2 中，因为 Python 内置的 `re` 引擎拒绝了“后顾变长断言” `(?<=v|version )`，所以你被迫使用了“捕获组”作为绕过手段。
但其实在很多现代语言（如 .NET, Java）或者 Python 的第三方库 `regex` 中，变长的后顾断言是完全合法的。

请你化身为正则引擎底层的 C 程序员推演一下：
如果我们要让游标站在当前位置，**向左倒退着**去匹配一个类似于 `.*` 这样长度未知的字符串，引擎底层的 NFA（非确定性有限状态自动机）在指针移动和状态回溯时，会面临怎样恐怖的“时空倒流”复杂度？
Python 标准库的核心开发者为了保证系统的稳定性，为什么宁可牺牲灵活性，也要对 `(?<=...)` 一刀切，强制要求长度固定？

回答：虽然我不知道，但是我猜测，应该是和主要是内存的创建问题，定长的话，我们就能使用数组，数组符合CPU缓存行读取的规则，这样就很快，不定长的话，缓存失效了。
"""
