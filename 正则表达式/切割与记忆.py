# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
"""
【节点 3.2：切割与记忆 (捕获组 () 与 Python 专属命名分组 (?P<name>))】

直觉模型：
- `()` (捕获组)：它是正则引擎内部的**手术刀和标本瓶**。你在长长的正则中，把想提取的局部核心数据用 `()` 包裹起来。引擎在匹配完一整段长文本后，会乖乖地把你放在 `()` 里的内容，切下来装进编号为 1, 2, 3... 的瓶子里供你取用。
- `(?P<name>...)` (命名捕获组)：Python 的专属魔法（其它语言也有类似实现但语法不同）。比起干巴巴的编号 1, 2, 3，你现在可以给标本瓶贴上标签了！比如 `(?P<ip>\d+\.\d+\.\d+\.\d+)`，提取后你可以直接通过字典的 key ("ip") 拿到这个数据，极大地提升了代码可读性。

致命陷阱/核心武器：
1. 编号地狱：在一个复杂的正则中，如果使用了七八个普通 `()`，当你写 `match.group(5)` 时，连你自己都会忘记第 5 个瓶子里装的是什么（是端口号？还是用户名？）。核心武器：工业界长串正则强推命名分组 `(?P<name>)` 配合 `match.groupdict()`，直接返回清晰的字典。
2. 嵌套陷阱：如果括号套着括号 `((A)(B))`，编号怎么算？记住唯一法则：**永远只数左括号 `(` 出现的顺序！**
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Dict, Optional

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(log_line: str) -> Optional[Dict[str, str]]:
    """
    【案发现场/初级代码】
    背景：你正在写一个 Nginx 访问日志解析器。
    你需要从一行日志中，分别提取出：IP地址、请求时间、HTTP方法、请求路径。
    """
    # 💣 致命错误：使用了大量的匿名捕获组，代码极难维护。如果将来要在中间加一个捕获组，后面的编号全都要错位修改。
    # 日志格式示例: 192.168.1.100 - [10/Oct/2023:13:55:36] "GET /api/v1/users HTTP/1.1"
    pattern = r"(\d+\.\d+\.\d+\.\d+)\s+-\s+\[(.*?)\]\s+\"([A-Z]+)\s+(.*?)\s+HTTP"
    match = re.search(pattern, log_line)

    if match:
        return {
            "ip": match.group(1),
            "timestamp": match.group(2),
            "method": match.group(3),
            "path": match.group(4),
        }
    return None


def architecture_engine(log_line: str) -> Optional[Dict[str, str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    使用带有 Python 命名分组 `(?P<name>...)` 的正则表达式。
    你需要为以下 4 个字段命名：
    - `ip`: 匹配 IP 地址 (例如 192.168.1.100)
    - `timestamp`: 匹配中括号内的时间戳 (例如 10/Oct/2023:13:55:36)
    - `method`: 匹配 HTTP 方法 (例如 GET, POST)
    - `path`: 匹配请求路径 (例如 /api/v1/users)
    """

    # TODO 1: 重构上面的 pattern，给每一个用于提取的括号，装上命名标签 (?P<name>...)
    # 提示：可以直接照抄上级代码的正则本体逻辑，但必须注入命名语法。
    pattern = r"(?P<ip>\d+\.\d+\.\d+\.\d+)\s+-\s+\[(?P<timestamp>.*?)\]\s+\"(?P<method>[A-Z]+)\s+(?P<path>.*?)\s+HTTP"

    match = re.search(pattern, log_line)

    if match:
        # TODO 2: 放弃丑陋的 group(1), group(2)。
        # 请调用 Match 对象极其优雅的 groupdict() 方法，一行代码返回包含所有命名分组的字典。
        result_dict: Dict[str, str] = match.groupdict()  # 修改这里
        return result_dict

    return None


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    nginx_log: str = (
        '192.168.1.100 - [10/Oct/2023:13:55:36] "GET /api/v1/users HTTP/1.1"'
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        result = architecture_engine(nginx_log)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证
    expected_dict: Dict[str, str] = {
        "ip": "192.168.1.100",
        "timestamp": "10/Oct/2023:13:55:36",
        "method": "GET",
        "path": "/api/v1/users",
    }

    if result != expected_dict:
        raise AssertionError(
            f"❌ 字典解析失败！\n"
            f"预期: {expected_dict}\n"
            f"实际: {result}\n"
            f"提示：命名语法 (?P<name>) 写对了吗？是否正确调用了 match.groupdict()？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功掌握了优雅的命名手术刀。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
你现在已经学会了用 `(?P<name>)` 和 `.groupdict()` 直接将日志切片成了字典。
假设你正在开发一个日志解析的开源库，用户可以自定义他们想要提取的字段名。
某个恶意用户输入了这样的恶意命名分组格式：`(?P<2bad_name>\d+)` 或者 `(?P<sys.path>\d+)`。

请在脑海中推演：
Python 正则引擎在编译这个带有命名分组的正则时，会对 `?P<...>` 里面的变量名进行什么样的底层约束？
为什么它必须施加这种约束？（提示：思考一下 `.groupdict()` 返回的字典 key，通常可以直接作为 JSON 的键，或者被解包 `**kwargs` 传递给 Python 函数）。

回答：我觉得应该是将name作为字典的key，印象它必须是可哈希的，不然.groupdict()也不能用。
"""
