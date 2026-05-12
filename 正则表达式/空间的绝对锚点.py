# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 1.3：空间的绝对锚点 (绝对边界 ^ $ 与极其容易错用的单词边界 \\b)】

直觉模型：
之前的量词和字符类，定义的是“吃什么”、“吃多少”。而边界断言（Anchors）定义的是“**在哪里吃**”。它们本身不消耗任何字符（属于零宽断言），仅仅是一把锁。
- `^`：字符串的绝对开头。游标必须死死卡在文本的第一个字符之前。
- `$`：字符串的绝对结尾。游标必须到达文本的最后一个字符之后。
- `\b` (Word Boundary)：单词边界。这是一个极其抽象的概念，它隐藏在 `\w` (单词字符，如字母数字下划线) 和 `\W` (非单词字符，如标点、空格) 的**交界处**。

致命陷阱/核心武器：
1. `match` 和 `search` 的误区：很多人用 `re.search(r"123", text)` 来校验用户输入的验证码是否为 "123"。如果用户输入 "x123y"，依然能通过校验！核心武器：格式严格校验时，必须用 `^` 和 `$` 锁死首尾：`r"^123$"`。
2. 词中词错杀：想要在日志中提取单纯的 `bug`，如果直接写 `bug`，会把 `debug` 和 `bugfix` 也提取出来。核心武器：使用 `\b` 卡住两头：`r"\bbug\b"`。
3. `\b` 的转义血案：在 Python 基础字符串中，`\b` 表示退格符 (Backspace)。如果不加 `r""`，正则引擎拿到的就是一个退格键，匹配永远失败。核心武器：防化服 `r""` 绝不能脱！
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(
    log_text: str, auth_tokens: List[str]
) -> Tuple[List[str], List[str]]:
    """
    【案发现场/初级代码】
    背景：你正在负责一个微服务的安全网关日志分析。
    任务 1：从海量日志中统计出单纯的 "error" 这个词的出现次数（不能把 terror、error_code 算进去）。
    任务 2：验证一批用户提交的授权 Token，合法的 Token 必须且只能是严格的 6 位十六进制代码（如 #A1B2C3）。
    """
    # 💣 致命错误 1：没有加边界，导致把 terror 里面的 error 也挖出来了。
    error_pattern: str = r"error"

    # 💣 致命错误 2：没有锁定绝对首尾空间，导致 "hack_#1a2b3c_injection" 这种恶意字符串也能通过匹配！
    hex_token_pattern: str = r"#[a-fA-F0-9]{6}"

    errors: List[str] = re.findall(error_pattern, log_text)

    valid_tokens: List[str] = []
    for token in auth_tokens:
        if re.search(hex_token_pattern, token):
            valid_tokens.append(token)

    return errors, valid_tokens


def architecture_engine(
    log_text: str, auth_tokens: List[str]
) -> Tuple[List[str], List[str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 提取出单纯的单词 "error"（区分大小写）。即使它被括号、逗号等标点符号包裹（例如 "(error)" 或 "error,"），也应该被提取出来。但坚决拒绝 "terror" 或 "errors"。
    2. 严格过滤 `auth_tokens` 列表，只有完全由一个 `#` 加上 6 位十六进制字符组成的字符串，才允许放入 `valid_tokens` 列表。
    """
    # TODO 1: 思考如何利用“单词边界”来保护 error 不被前后的字母污染
    exact_error_pattern: str = r"\berror\b"

    # TODO 2: 思考如何把这把锁钉死在字符串的最前端和最后端，不给恶意前缀/后缀留一丝空间
    strict_hex_pattern: str = r"^#[a-fA-F0-9]{6}$"

    errors: List[str] = (
        re.findall(exact_error_pattern, log_text) if exact_error_pattern else []
    )

    valid_tokens: List[str] = []
    if strict_hex_pattern:
        for token in auth_tokens:
            # 提示：仍然使用 re.search，但让正则模式本身去强制首尾匹配
            if re.search(strict_hex_pattern, token):
                valid_tokens.append(token)

    return errors, valid_tokens


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    dirty_log: str = (
        "The system encounters a terror when processing the (error). Also error_code 500 is a severe error!"
    )
    dirty_tokens: List[str] = [
        "#1a2b3c",  # 正常 Token
        "invalid_#1a2b3c",  # 恶意前缀注入
        "#abcdef7",  # 长度越界 (7位)
        "#FF0000",  # 正常 Token (大写)
        " #112233",  # 前面暗藏空格
    ]

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        errors, valid_tokens = architecture_engine(dirty_log, dirty_tokens)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_errors: List[str] = ["error", "error"]
    expected_tokens: List[str] = ["#1a2b3c", "#FF0000"]

    if errors != expected_errors:
        raise AssertionError(
            f'❌ Error提取失败！\n预期: {expected_errors}\n实际: {errors}\n提示：你的边界卡住了吗？防化服 r"" 穿了吗？'
        )

    if valid_tokens != expected_tokens:
        raise AssertionError(
            f"❌ Token校验被击穿！\n预期: {expected_tokens}\n实际: {valid_tokens}\n提示：黑客绕过了你的正则墙！你是不是忘了锁死字符串的开头和结尾？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功守住了系统的边界防御。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
你刚刚用 `\b` 成功锁定了 `error` 这样的纯字母单词。
现在假设一个场景：你的技术博客网站遭遇了恶意爬虫，你需要从日志中精准提取出一个被高频搜索的编程语言关键字：“C++”。
你直觉性地写下了：`r"\bC\+\+\b"`

请在脑海中推演：当你运行 `re.findall(r"\bC\+\+\b", "I love C++ programming")` 时，结果会是什么？
为什么这行看似完美的“边界+转义”正则，在物理底层会彻底失效，根本无法匹配出 `C++`？
(提示：回想一下 `\b` 的本质定义——它是谁和谁的交界处？`+` 号属于哪一种字符？)

回答：\b的本质是在\w和\W之外的字符，+属于\W，因为只会有C，没得++或者是空的。
"""
