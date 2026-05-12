# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 4.2：灾难性回溯 (Catastrophic Backtracking)】

直觉模型：
当贪婪量词（`*`, `+`）遇到嵌套（比如 `(A+)+` 或 `(A*)*`），并且字符串的末尾匹配失败时，引擎不会立刻报错，而是会认为“是不是我刚刚贪婪的时候吃错了？我吐出来一点点试试”。
如果字符串非常长，引擎就会陷入疯狂的“吃进去 -> 吐出来 -> 换种组合吃 -> 再吐出来”的排列组合地狱。时间复杂度瞬间从 O(N) 暴增到恐怖的 O(2^N) 甚至更高。

致命陷阱/核心武器：
1. 经典的雪崩现场：尝试用 `^([a-zA-Z0-9]+\s?)+$` 校验一个由空格隔开的长名字。
   - 当输入合法时："John Doe Smith"，引擎一路推平，瞬间通过。
   - 当输入在末尾多了一个非法字符时："John Doe Smith!!!!!!"
   - 灾难降临：引擎推到末尾碰到 `!` 发现失败，它开始疯狂回溯：
     是把 "John Doe Smith" 作为一个整体？
     还是把 "John Doe", "Smith" 分成两个词？
     还是 "John", "Doe Smith"？
     还是 "John", "Doe", "S", "m", "i", "t", "h"？
     只要你的字符串够长，服务器 CPU 瞬间 100% 飙红，直到世界末日也不会出结果！这是黑客最常用的 ReDoS (Regular Expression Denial of Service) 攻击手段。

2. 物理武器：原子组/固化分组 (Atomic Grouping) `(?>...)`
   - Python 内置的 `re` 模块长期不支持原子组，只能用极其丑陋的黑魔法 `(?=(...))\1` 模拟。
   - 但！在现代 Python 版本（或使用工业级第三方库 `regex` 时），原子组是降服回溯的终极核武。
   - `(?>...)` 的物理意义：“**一旦你吃进去了，就把门焊死，绝对不准吐出来！就算匹配失败，直接报错，不准回溯！**” 引擎直接变成了无情碾压的终结者。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
import threading
from typing import Optional

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> bool:
    """
    【案发现场/初级代码】
    背景：你需要验证用户输入的标签列表，格式必须是纯字母加下划线，多个标签用逗号隔开。
    例如："python,java,c_plus_plus"
    """
    # 💣 致命错误：极其危险的嵌套量词 `(\w+,?)+`。
    # 内部 `\w+` 是贪婪的，外部 `+` 也是贪婪的，且 `,?` 是可选的。
    # 一旦文本末尾出现非法字符，引擎会在 `\w+` 组合切分上陷入指数级回溯。
    dangerous_pattern = r"^(\w+,?)+$"
    return bool(re.match(dangerous_pattern, text))


def architecture_engine(text: str) -> bool:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    我们要重写上面的危险正则，彻底消灭回溯炸弹。
    不用去硬拼原子组，我们用更优雅、结构更清晰的“字符类严格控制”法则。

    规则解析：
    一个合法的标签列表，必然是：
    开头是一个纯标签 (`\w+`)
    后面跟着 0 个或多个组合：(一个逗号，加一个纯标签)
    """

    # TODO: 放弃嵌套的 `(\w+,?)+`。
    # 写出一个结构极其严格的正则，确保：
    # 1. 第一个是单独的 `\w+`。
    # 2. 后面跟着 `(,\w+)*`。
    # 3. 必须用 ^ 和 $ 锁死首尾。
    # 这种写法引擎不需要在逗号和字母的边界上进行任何多余的排列组合猜测，直接实现 O(N) 的线性扫描！
    safe_pattern: str = r"^\w+(?:\,\w+)*$"

    return bool(re.match(safe_pattern, text))


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    # 模拟一个黑客发起的 ReDoS 攻击字符串：
    # 前面是 30 个合法的字母，最后故意放一个非法的感叹号！
    evil_payload: str = "a" * 30 + "!"

    start_time: float = time.time()

    # ---------------- 危险演示：引爆灾难 ----------------
    print("\n⚠️ 正在启动危险代码（如果卡死，请立即 Ctl+C 终止运行）...")

    # 我们用多线程来跑危险代码，如果 2 秒没结果直接杀死，防止你的电脑真宕机。
    # def run_dangerous():
    #     naive_or_broken_worker(evil_payload)

    # danger_thread = threading.Thread(target=run_dangerous)
    # danger_thread.daemon = True
    # danger_thread.start()
    # danger_thread.join(timeout=2.0)

    # if danger_thread.is_alive():
    #     print("💥 灾难发生！危险引擎已陷入指数级回溯地狱，CPU正在燃烧！")
    # else:
    #     print("❓ 危险引擎竟然跑完了？你的 CPU 可能强到离谱，或者 Python 优化了。")

    # ---------------- 安全校验：架构师登场 ----------------
    print("\n🛡️ 正在启动架构师安全代码...")
    try:
        # 安全引擎应该在 0.00x 秒内立刻识破黑客的诡计并返回 False
        safe_result = architecture_engine(evil_payload)
        if safe_result is True:
            raise AssertionError("❌ 你的安全引擎被黑客欺骗了，竟然返回了 True！")
    except Exception as e:
        raise AssertionError(f"❌ 安全引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    print(f"⏱️ 安全引擎瞬间完成拦截！总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功阻止了一场服务器宕机灾难。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
在上面的实战中，我们通过“重写正则结构” `^\w+(,\w+)*$` 成功消除了回溯灾难。
但假设在真实的工业界，因为业务逻辑过于极其复杂（比如校验嵌套的 HTML 标签），你很难通过这种重构来完全避免嵌套量词。

此时，除了使用更强大的引擎（带有原子组 `(?>...)` 的 `regex` 模块库）之外，
请在脑海中推演：在系统工程（System Engineering）层面，如果你作为后端架构师，为了绝对防御黑客通过 API 故意提交带有恶意的 ReDoS 攻击字符串（比如超长的、精心构造的脏数据）来打满你的 CPU，你应该在正则引擎的**上游**，部署哪些最简单、最暴力的物理防御手段？

回答：一般是超时机制或者是监控CPU使用
"""
