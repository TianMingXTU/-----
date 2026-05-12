# ================= 0. 终局任务简报 (The Final Mission) =================
"""
【节点 5.0：工业级脏数据清洗管道】

背景：
凌晨 3 点，公司的核心网关发生了连环崩溃。运维团队发来了一份巨大的错误日志 dump。
这份日志极其恶心：
1. 包含 INFO, WARNING, ERROR 等各种级别的日志，但级别标签的大小写完全是乱的（比如 [eRrOr], [WARNING]）。
2. ERROR 或 WARNING 的报错信息往往不是单行的！它们可能会携带一长串的 Traceback 堆栈，跨越多行，直到下一条日志的开头为止。
3. 里面混杂了大量的脏空格和空行。

你的任务：
提取出**所有属于警告 (WARNING) 或 错误 (ERROR)** 的日志条目（忽略 INFO 和 DEBUG 等），并且把每一条报警日志切片成清晰的字典结构，包含：
- `level`: 报警级别 (转成大写，例如 "ERROR")
- `time`: 发生时间
- `service`: 崩溃的微服务名称 (在中括号或尖括号里)
- `message`: 具体的报错内容（包含可能跨行的堆栈，但**绝对不能**吃掉下一条日志）

终极核武库：
- `re.I` (忽略大小写)
- `re.M` (多行模式，让 `^` 能够锚定每一行的开头)
- `re.S` (单行穿透，让 `.` 能吃掉换行符，提取多行堆栈)
- `re.X` (结构化编译，保持你的代码可维护)
- `(?=...)` (正向先行断言，用来探路，找到下一条日志的开头，但不要吃掉它)
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Dict

# ================= 2. 终局代码骨架 (The Architecture) =================


def final_crucible_engine(raw_log_blob: str) -> List[Dict[str, str]]:
    """
    TODO: 在此展现你真正的架构师实力。
    构建一个无懈可击的正则表达式，并使用流式迭代提取结果。
    """

    # TODO 1: 编写终极正则表达式 (必须使用 re.VERBOSE 格式)
    # 提示：
    # 1. 锚定行首的 `[` 开始。
    # 2. 捕获级别 (?P<level>ERROR|WARNING) (记得开启 re.I)。
    # 3. 提取时间 (?P<time>...)。
    # 4. 提取服务名 (?P<service>...)，注意服务名周围可能有 - 符号包围。
    # 5. 提取消息 (?P<message>.*?)，注意这里是跨行的。
    # 6. 终极防御：消息应该在哪里停下？在字符串的绝对末尾 (\Z)，或者下一条日志的行首 (?=^\[)。

    master_pattern = r"""
    (?P<level>\[ERROR\]|\[WARNING\])
    \s
    (?P<time>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})
    \s-\s
    (?P<service>\<.*?\>)
    \s-\s
    (?P<message>.*?)\n+
    (?=^\[|\Z)
    """

    # TODO 2: 注入灵魂（组合四把神兵利器）
    # 提示：re.I | re.M | re.S | re.VERBOSE
    compiled_engine = re.compile(master_pattern, flags=re.I | re.M | re.S | re.VERBOSE)

    results: List[Dict[str, str]] = []

    # TODO 3: 流式收割
    # 请使用 re.finditer 来避免 OOM，遍历所有的 Match 对象
    for match in compiled_engine.finditer(raw_log_blob):
        data = match.groupdict()
        data["level"] = data["level"].upper().lstrip("[").rstrip("]")
        data["service"] = data["service"].lstrip("<").rstrip(">")
        results.append(data)

    return results


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 终局之战：开始执行黑盒测试 ---")

    # 这是一份充满恶意的真实业务日志
    disaster_log: str = (
        "[InFo] 2026-05-12 01:00:00 - <Auth> - Normal login.\n"
        "[eRrOr] 2026-05-12 01:05:12 - <Database_Core> - Connection timeout.\n"
        "Traceback (most recent call last):\n"
        '  File "db.py", line 42, in connect\n'
        "TimeoutError: db is dead.\n"
        "[WARNing] 2026-05-12 01:06:00 - <Cache-Node-1> - Memory usage 95%!\n"
        "[inFO] 2026-05-12 01:07:00 - <System> - Heartbeat OK."
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        results = final_crucible_engine(disaster_log)
    except Exception as e:
        raise AssertionError(
            f"❌ 引擎在最终战场崩溃了！死因 -> {type(e).__name__}: {e}"
        )

    total_cost: float = time.time() - start_time

    # 2. 严苛的断言拦截
    if len(results) != 2:
        raise AssertionError(
            f"❌ 提取数量错误！预期只提取 ERROR 和 WARNING 共 2 条，实际提取了 {len(results)} 条。"
        )

    # 校验第一条报错 (跨行测试)
    error_log = results[0]
    if error_log.get("level") != "ERROR":
        raise AssertionError("❌ 级别转换错误或未提取到 ERROR。")
    if error_log.get("service") != "Database_Core":
        raise AssertionError(f"❌ 服务名提取失败，实际为: {error_log.get('service')}")
    if "TimeoutError: db is dead." not in error_log.get("message", ""):
        raise AssertionError(
            "❌ 跨行堆栈提取失败！你的 `.` 没有穿透换行符，或者 `.*?` 提早结束了。"
        )

    # 校验第二条警告 (边界测试)
    warn_log = results[1]
    if warn_log.get("level") != "WARNING":
        raise AssertionError("❌ 级别转换错误或未提取到 WARNING。")
    if warn_log.get("service") != "Cache-Node-1":
        raise AssertionError("❌ 带有横杠的服务名提取失败。")

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("🏆 恭喜通关！你已斩杀这只混沌巨兽，成为了真正的正则架构师！")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：正则表达式的黄昏与黎明) =================
"""
🧠 慢思考拷问 (首席架构师的终极一问)：
恭喜你走到了这里，你已经掌握了人类编写文本模式匹配的最高效物理工具。
但现在，大语言模型（LLM）时代已经到来。很多人说：“遇到脏数据，我直接写个 prompt 扔给 LLM 让它输出 JSON 就行了，谁还写这反人类的正则表达式？”

作为一名即精通大模型工程，又掌握了底层正则引擎的开发者，请你客观地推演：
1. 在工业级数据清洗中，纯靠 LLM 替代正则表达式，会面临哪些致命的系统工程问题？（提示：思考吞吐量、成本、延迟与确定性）。
2. 在未来的系统架构中，正则表达式和 LLM 应该是一种怎样的共生关系？你能构想出一个将两者完美结合的清洗管道架构吗？

回答：LLM傻傻的，输出是不确定的，是概率学。使用高级LLM那就花费贵，使用低级LLM就解析失败。而且还慢。
未来的话应该是有限正则表达式，使用LLM进行兜底。
"""
