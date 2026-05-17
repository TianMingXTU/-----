# ================= 0. 干活指南与 API 映射 (快思考) =================
"""
【业务场景/功能节点名称】：第一阶段 - 描述符协议 (Descriptor Protocol) - 字段级数据校验

🧠 实用直觉：
别管底层 CPython 怎么找属性的字典树，你就把描述符当成一个【属性外挂路由器】。
场景：当你发现业务代码里到处都是 `if age < 0: raise ValueError`，或者你想自己撸一个类似 Django ORM 的字段映射时，直接掏出描述符。把校验逻辑封装在描述符里，宿主类直接挂载即可。

🛠️ 核心 API 兵器谱：
- `__set_name__(self, owner: type, name: str) -> None`  # 自动获取宿主类中绑定的变量名，省去手动传参的破事。
- `__get__(self, instance: object | None, owner: type) -> Any` # 拦截读取。注意 instance 为 None 时代表是通过类本身访问。
- `__set__(self, instance: object, value: Any) -> None` # 拦截赋值，做类型/范围校验，并将干净的数据存入宿主实例。
- `__delete__(self, instance: object) -> None` # 拦截 `del obj.attr`，工程中通常做软删除或资源清理标识。
"""

# ================= 1. 环境与依赖准备 =================
from typing import Any, Optional, Type

# ================= 2. 搬砖实战场 (Pragmatic Battleground) =================

"""
【案发现场：干活时的低级错误】
很多工程师第一次接触描述符时最容易踩的“共享状态”天坑。代码单测能跑，一上线高并发全乱套。
"""


class RookieIntField:
    def __init__(self) -> None:
        # 💥 致命错误：把数据存在了描述符实例本身！
        self._value: int = 0

    def __get__(self, instance: Optional[object], owner: Type) -> int:
        return self._value

    def __set__(self, instance: object, value: int) -> None:
        self._value = value  # 💥 只要有多个宿主实例并发修改，数据立刻串线！


"""
【实战干活：TODO】
背景说明：现在你需要给核心模型写一个严谨的整数校验字段 `ValidatedInt`。
实战要求：
1. 要求能限制最小值 (min_val) 和最大值 (max_val)。
2. 必须利用 `__set_name__` 自动获取变量名，拒绝硬编码。
3. 数据必须正确隔离，存入 `instance.__dict__`。
4. 赋值时如果越界或类型不对，抛出标准的 ValueError 或 TypeError。
"""


class ValidatedInt:
    def __init__(self, min_val: int, max_val: int) -> None:
        self.min_val: int = min_val
        self.max_val: int = max_val
        self.name: str = ""  # 等待 __set_name__ 注入

    def __set_name__(self, owner: Type, name: str) -> None:
        # TODO 1: 保存变量名。
        pass

    def __get__(self, instance: Optional[object], owner: Type) -> Any:
        # TODO 2: 拦截读取。
        # 提示：如果 instance 为 None，说明是类调用 (UserModel.age)，应该返回什么？
        # 如果是实例调用，从哪里把真正的值取出来？
        pass

    def __set__(self, instance: object, value: Any) -> None:
        # TODO 3: 拦截赋值。
        # 第一步：校验 value 的类型（必须是 int）和范围（min_val <= value <= max_val）。异常直接 raise。
        # 第二步：把校验通过的 value 安全地塞进 instance 的专属空间里。
        pass


class UserModel:
    # 业务侧直接爽快调用，把校验逻辑全部外包，保持主逻辑干净
    age = ValidatedInt(min_val=0, max_val=150)
    level = ValidatedInt(min_val=1, max_val=99)

    def __init__(self, age: int, level: int) -> None:
        self.age = age
        self.level = level


# ================= 3. 黑盒测试 (Test Cases：交差验收) =================
def test_crucible() -> None:
    # 1. 正常实例化
    user1 = UserModel(age=25, level=10)
    user2 = UserModel(age=30, level=99)

    # 2. 验证数据隔离（Rookie 错误终结者）
    assert user1.age == 25
    assert user2.age == 30, "💥 测试失败：数据串线了，user2 的年龄变成了 user1 的！"

    # 3. 验证校验逻辑
    try:
        user1.age = 200
        print("💥 测试失败：异常拦截失效，允许了非法数据！")
    except ValueError:
        pass  # 预期内的拦截

    # 4. 验证 __set_name__ 是否生效
    assert (
        "age" in user1.__dict__
    ), "💥 测试失败：数据没有正确存入 instance.__dict__，检查你存储时用的 key！"

    print("✅ QA 测试通过！代码成功合入主分支。")


# ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) =================
"""
🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
【真实事故场景模拟】：
假设你图省事，用了上面的 `RookieIntField` 写法。代码上线 3 小时后，现场人员接到了疯狂的投诉：“为什么我一修改我的年龄，别人的年龄也跟着变了？！”

👉 救火任务：
结合刚才的事故，在 `__set__` 中直接写 `self._value = value` 为什么会导致所有 `UserModel` 实例强制共享同一个值？描述符对象（`ValidatedInt`）和宿主类对象（`UserModel`）在内存中到底是什么关系（1对1 还是 1对多）？
"""
