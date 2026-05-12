# ================= 0. 知识点讲解 (快思考：直觉与心法) =================
r"""
【节点 1.1：原子的力量 (普通字符、元字符、字符类与 Raw 转义地雷)】

直觉模型：
把正则引擎想象成一个“吃豆人 (Pac-Man)”，游标 (Cursor) 就是它的嘴巴，待匹配的字符串是一条赛道。
- 普通字符（如 `a`, `1`）：吃豆人只能严格吃掉一模一样的豆子。
- 元字符（如 `\d`, `\w`, `\s`）：吃豆人拥有了“分类识别器”，可以一口吞下任何数字、字符或空白。
- 字符类 `[...]` 与取反 `[^...]`：你给吃豆人制定了一份“专属菜单”（只吃这些）或“过敏清单”（碰到这些绝对不吃）。
- Python Raw 字符串 `r""`：这是你给吃豆人穿上的“防化服”。如果不加 `r`，Python 解释器会先于正则引擎处理字符串，把你辛辛苦苦写的转义符吃掉，甚至把 `\n` 变成换行符，导致引擎拿到的规则面目全非。

致命陷阱/核心武器：
1. 转义地雷：在正则中匹配物理世界里的一个反斜杠，极易引发转义灾难。核心武器：永远、绝对、无脑地在正则模式前加上 `r`。
2. `\w` 的背叛：很多人以为 `\w` 只包含英文字母和数字，但在 Python 3 中，它默认包含下划线 `_`，甚至包含大部分 Unicode 字符（如中文）。核心武器：在需要严谨时，老老实实用显式区间。
3. `[^]` 取反的范围杀伤：`[^a-z]` 会匹配到换行符、标点符号等所有非小写字母的原子，极易导致游标越界。
"""

# ================= 1. 依赖导入 (Imports) =================
import time
import re
from typing import List, Tuple

# ================= 2. 代码骨架 (Starter Code：实战与排雷) =================


def naive_or_broken_worker(text: str) -> Tuple[List[str], List[str]]:
    """
    【案发现场/初级代码】
    背景：你正在清洗一批刚刚从互联网抓取的、极其脏乱的大语言模型（LLM）预训练原始语料。
    初级工程师试图提取里面的“Windows 本地文件路径”和合法的“十六进制用户 ID”。
    """
    # 💣 致命错误 1：没有使用 r""，导致 \t 和 \n 被提前解释为制表符和换行符
    # 💣 致命错误 2：用 \w 匹配 ID，放过了下划线、大写字母甚至中文字符
    # 💣 致命错误 3：方括号未转义，且随意使用了通配符 .
    path_pattern: str = "C:\test\nlp_data\.*"
    id_pattern: str = "[ID-\w+]"

    paths: List[str] = re.findall(path_pattern, text)
    ids: List[str] = re.findall(id_pattern, text)
    return paths, ids


def architecture_engine(text: str) -> Tuple[List[str], List[str]]:
    """
    TODO: 在此实现你的高阶架构逻辑
    要求：
    1. 提取出以 `C:\` 开头，且只包含英文字母、数字、下划线 `_` 和反斜杠 `\` 的完整 Windows 路径（不能匹配到换行符或空格）。
    2. 提取出严格格式为 `[ID-xxx]` 的标识，其中 `xxx` 必须且只能是小写字母 `a` 到 `f` 和数字 `0` 到 `9`，且至少包含一个字符。不能包含下划线或任何大写字母。
    """
    # TODO 1: 穿上防化服，思考如何匹配字面量反斜杠，以及如何使用字符类划定合法的路径字符集合。
    path_pattern = r"(C:\\[a-z0-9A-Z\_\\]+)"

    # TODO 2: 思考如何让引擎物理识别字面量的方括号，以及如何在内部使用严格的区间隔离。
    id_pattern: str = r"\[ID-[a-f0-9]+\]"

    paths: List[str] = re.findall(path_pattern, text) if path_pattern else []
    ids: List[str] = re.findall(id_pattern, text) if id_pattern else []

    return paths, ids


# ================= 3. 黑盒测试 (Test Cases：工业级无情审判) =================
def test_crucible() -> None:
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    dirty_llm_corpus: str = (
        "Dataset loaded from C:\\Data\\train_corpus_01 \n"
        "Warning: C:\temp\nlp_data is missing! \n"
        "Author IDs: [ID-a4f9], [ID-8Bcd], [ID-test_user], [ID-7721] \n"
        "Backup at C:\\models\\v1_checkpoint_final "
    )

    start_time: float = time.time()

    # 1. 引擎启动
    try:
        paths, ids = architecture_engine(dirty_llm_corpus)
    except Exception as e:
        raise AssertionError(f"❌ 引擎直接崩溃了！死因 -> {type(e).__name__}: {e}")

    total_cost: float = time.time() - start_time

    # 2. 核心架构与逻辑验证 (严苛的 Assert 拦截)
    expected_paths: List[str] = [
        "C:\\Data\\train_corpus_01",
        "C:\\models\\v1_checkpoint_final",
    ]
    expected_ids: List[str] = ["[ID-a4f9]", "[ID-7721]"]

    if paths != expected_paths:
        raise AssertionError(
            f"❌ 路径提取失败！\n预期: {expected_paths}\n实际: {paths}\n提示：你的游标是不是吃错了东西，或者没加上 r 导致转义炸了？"
        )

    if ids != expected_ids:
        raise AssertionError(
            f"❌ ID提取失败！\n预期: {expected_ids}\n实际: {ids}\n提示：你是不是被 \\w 骗了，或者没有正确转义正则本身的保留字符？"
        )

    print(f"⏱️ 引擎总耗时: {total_cost:.4f} 秒")
    print("✅ All Tests Passed! 恭喜 AC！你成功跨越了这片雷区。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 (灵魂拷问：系统级降维打击) =================
"""
🧠 慢思考拷问 (首席架构师的灵魂一问)：
代码跑通只是及格。
在这里，我会假设一个极其极端的工业场景：如果你的清洗管道正在对一个高达 TB 级的多语种自然语言训练集进行逐行清洗，而你在所有需要提取“仅限英文字母或数字”的字段（例如某些特定 Token）时，为了图方便都使用了 `\w`。

请在脑海中推演：当你把这段代码部署到服务器上，开始高速清洗来自全球各地的混合语料时，会发生什么灾难？下游的 LLM 训练框架会因此接收到什么不可预知的脏数据？

回答：/w会返回字母、数字、_。它会加入下划线以及其他的encode的字符，比如中文，导致数据进行脏化。
"""
