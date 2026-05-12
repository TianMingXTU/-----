# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 2.1：搜索与匹配的鸿沟 (re.search, re.match, re.fullmatch 的误用灾难)】

直觉模型：
在 Python 的 `re` 模块中，同样的正则表达式，交给不同的“执行官”，会得到完全不同的结果：
- `re.search` (游猎者)：拿着你的照片，在茫茫人海（整个字符串）中从左到右寻找，只要找到第一个长得像的，立刻带回来（返回 Match 对象）。
- `re.match` (门神)：它极其死板，**永远只站在字符串的绝对开头处（索引 0）**。如果字符串的第一个字符就不符合你的正则，它直接摇头返回 None。它等价于在你的正则最前面隐式加上了 `^`。
- `re.fullmatch` (验明正身)：它是最严苛的法官。不仅要求从头开始匹配，还要求必须匹配到字符串的最后一个字符，差一个标点符号都不行。它等价于在你的正则首尾隐式加上了 `^...$`。

致命陷阱/核心武器：
1. 用 `match` 找日志：很多新手想找日志中间的错误码，随手写了 `re.match(r"ERROR_CODE", log)`。结果永远返回 None，因为错误码不在行的最开头。核心武器：换成 `re.search`。
2. 用 `match` 校验手机号：前端传来的手机号，新手用 `re.match(r"1\d{10}", phone)` 校验。黑客传入 `"13800138000_drop_table_users"`，居然校验通过了！因为 `match` 只管开头，不管结尾。核心武器：数据清洗/格式校验必须用 `re.fullmatch`！
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import Optional

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(log_line: str, pin_code: str) -> tuple[bool, bool]:
    """
    【案发现场/初级代码】
    背景：你正在编写一个高安全级别的系统防火墙。
    任务 1：判断一行日志是否以 "CRITICAL" 开头（门神机制）。
    任务 2：严格校验用户输入的 PIN 码，必须且只能是 4 位纯数字。
    """
    critical_pattern: str = r"CRITICAL"
    pin_pattern: str = r"\d{4}"

    # 💣 致命错误 1：想做“开头匹配”，却用了 search。这会导致日志中间包含 CRITICAL 也会被误判。
    is_critical: bool = bool(re.search(critical_pattern, log_line))

    # 💣 致命错误 2：想做“严格校验”，却用了 match。黑客输入 "1234_hack" 也能通关。
    is_valid_pin: bool = bool(re.match(pin_pattern, pin_code))

    return is_critical, is_valid_pin


def architecture_engine(log_line: str, pin_code: str) -> tuple[bool, bool]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    注意，我们【不修改】正则表达式本身（保持原始状态），而是通过调用正确的 Python API 来实现正确的逻辑。
    1. 确保只有真正在最开头出现 "CRITICAL" 的日志，才返回 True。
    2. 确保 PIN 码必须是完完整整的 4 位数字，多一个字符或少一个字符都返回 False。
    """
    critical_pattern: str = r"CRITICAL"
    pin_pattern: str = r"\d{4}"

    # TODO 1: 替换掉 search，使用能真正卡住开头的 API
    is_critical: bool = bool(re.match(critical_pattern, log_line))

    # TODO 2: 替换掉 match，使用最严苛的全量校验 API
    is_valid_pin: bool = bool(re.fullmatch(pin_pattern, pin_code))

    return is_critical, is_valid_pin


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time: float = time.time()

    # 测试集 1：测试日志级别判断
    true_critical = "CRITICAL: System core melted!"
    fake_critical = "INFO: The word CRITICAL was mentioned."

    # 测试集 2：测试 PIN 码格式
    perfect_pin = "8520"
    hacked_pin = "8520x"

    try:
        # 1. 验证日志
        tc_res, _ = architecture_engine(true_critical, perfect_pin)
        fc_res, _ = architecture_engine(fake_critical, perfect_pin)

        # 2. 验证 PIN
        _, pp_res = architecture_engine(true_critical, perfect_pin)
        _, hp_res = architecture_engine(true_critical, hacked_pin)

    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 3. 断言拦截
    if not tc_res:
        raise AssertionError("❌ 门神失职：真正以 CRITICAL 开头的日志被拦截了！")
    if fc_res:
        raise AssertionError(
            "❌ 门神眼瞎：伪装的 CRITICAL（在日志中间）居然通过了检查！你是不是用了 search？"
        )

    if not pp_res:
        raise AssertionError("❌ 法官错杀：完美的 4 位数字 PIN 被拒绝了！")
    if hp_res:
        raise AssertionError(
            "❌ 法官受贿：带有尾缀的 4 位数字 PIN (8520x) 居然校验通过了！你是不是还在用 match？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功跨越了 Python 接口调用的鸿沟。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上一节（1.3）中，我们学习了使用 `^` 和 `$` 配合 `re.search` 来实现绝对边界锁定：
`re.search(r"^\d{4}$", text)`

在本节中，我们学习了不修改正则，而是改变 API：
`re.fullmatch(r"\d{4}", text)`

请在脑海中推演：
这两种写法在逻辑上是完全等价的。但在工业界的大规模框架（如 Django, FastAPI 的路由底层）中，核心开发者为什么强烈倾向于使用 `re.fullmatch()`，而不是到处写 `^` 和 `$` 配合 `search`？
提示：从代码的可读性（心智负担）、复用性（同一个正则既能拿来部分提取，又能拿来全量校验）角度去思考。

回答：1、使用^不好读，增加了心智负担，^也能做取反，这样的话，复用性虽然很好，但是呢，不够直观。
"""
