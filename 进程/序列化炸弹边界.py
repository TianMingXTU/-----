# ================= 0. 知识点讲解 =================
"""
【Pickle 序列化炸弹边界 (Serialization Limits)】

直觉模型：
多进程的内存是物理隔离的。不管你是用 Queue、Pipe，还是用 ProcessPoolExecutor 派发任务，
只要你把一个 Python 对象从主进程传给子进程（或者反过来），Python 底层都必须做一个动作：
**序列化 (Pickle)** —— 把对象变成一串二进制字节流，通过管道传过去，再在对面“反序列化”还原。

致命陷阱：
不是所有东西都能被变成“肉干”（二进制流）！
如果遇到以下几种东西，底层的 `pickle` 模块会当场崩溃，抛出异常，导致你的多进程程序瞬间暴毙：
1. 匿名函数 (Lambda) 和 嵌套函数 (Nested/Local functions/Closures)：因为它们没有在模块级别的全局名称。
2. 操作系统级别的句柄：打开的文件对象 (File objects)、网络连接套接字 (Sockets)、数据库连接 (DB Connections)。
3. 多进程同步原语：你不能把一个普通的 `Lock` 或 `Semaphore` 当作参数丢进 Pool 里传给别人（会报 RuntimeError 或 TypeError）。

解决方案：
- 函数必须定义在模块的最外层（全局作用域）。
- 数据库连接和文件句柄，必须在子进程启动后，由子进程**自己去创建和打开**，绝不能由主进程创建后传过去！
"""

# ================= 1. 依赖导入 (Imports) =================
import concurrent.futures
import multiprocessing

# ================= 2. 代码骨架 (Starter Code) =================


# --- 💣 这里是案发现场，请仔细观察 ---
def bad_architecture_engine(data_list):
    """
    【业务场景】这是一个初级工程师写的代码。
    他觉得把处理函数写在主函数里面“看起来很内聚”，并且他还随手传了一个 Lock 进去。
    你运行一下就会发现，这段代码会直接引发连环爆炸（PicklingError / TypeError / AttributeError）。
    """

    # 陷阱 1：这是一个局部嵌套函数 (Local Function)
    def calculate_square(x, dummy_lock):
        # 假装用到锁
        with dummy_lock:
            return x * x

    # 陷阱 2：主进程创建了一把锁，企图通过 Pool 传给子进程
    my_lock = multiprocessing.Lock()

    print("[主进程] 企图启动进程池并发计算...")

    # 试图把 局部函数 和 Lock 塞进进程池
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        # 这里会直接炸开！
        futures = []
        for num in data_list:
            futures.append(executor.submit(calculate_square, num, my_lock))

        results = [f.result() for f in futures]

    return results


# --- 🛠️ TODO: 请在下方重构出一个完美运转的架构 ---

# TODO 1: 把那个嵌套的函数抽离出来，放到模块级别（全局作用域）。


def safe_calculate_square(x):
    return x * x


def robust_architecture_engine(data_list):
    """
    TODO 2: 在这里实现你重构后的安全并发逻辑。
    要求：
    1. 成功计算 data_list 中每个元素的平方。
    2. 绝对不能把 Lock 通过 executor.submit 传过去！（如果子进程非要用锁怎么办？在这个简单的数学计算场景里，其实根本不需要锁，直接删掉锁的传递逻辑即可）。
    """
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
        futures = []
        for num in data_list:
            futures.append(executor.submit(safe_calculate_square, num))

        results = [f.result() for f in futures]

    return results


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    data = [1, 2, 3, 4, 5]

    # 测试 1: 验证原代码是否真的会炸 (探雷)
    try:
        bad_architecture_engine(data)
        raise AssertionError(
            "❌ 灾难：这段破代码竟然跑通了？不可能！一定是你修改了案发现场！"
        )
    except Exception as e:
        print(f"✅ 探雷成功：原代码确实爆炸了，死因是 -> {type(e).__name__}: {e}")

    # 测试 2: 验证你重构的代码
    try:
        results = robust_architecture_engine(data)
        if set(results) != {1, 4, 9, 16, 25}:
            raise AssertionError(f"❌ 逻辑错误：计算结果不对，你的结果是 {results}")
        print("✅ 测试 2 通过：重构成功！跨越了 Pickle 序列化边界。")
    except Exception as e:
        raise AssertionError(
            f"❌ 依然爆炸：你的重构代码还是触发了序列化错误 -> {type(e).__name__}: {e}"
        )

    print("🎉 All Tests Passed! 恭喜 AC！你懂得了不要什么垃圾都往管道里塞。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
在上面的 TODO 2 中，我们通过“直接删掉 Lock 参数”规避了序列化锁的错误（因为数学计算本来就不需要锁）。

但在真实的极端工业场景下：如果我们**真的必须**在使用 `ProcessPoolExecutor` 时，
让所有池子里的子进程共享一把锁（比如它们都要向同一个文件里写日志，防止写乱），
既然主进程创建的 `multiprocessing.Lock()` 不能作为参数传给 `executor.submit`，
那你该如何把这把锁交给子进程？

（提示 1：回忆上一关讲的，如何绕过 `Pool` 直接利用操作系统的机制？如果在创建池子时，给每个子进程指定一个 `initializer` 初始化函数呢？）
（提示 2：回忆战区零的节点 1.4，除了锁，还有什么东西可以在多进程间“代理”共享？）
如果不知道具体 API，用自然语言说出你的架构思路即可！

回答：我们在子线程里面加一把锁，但是锁就不是全局的了，但是我们可以整一个全局锁，就是全局共享那种，但是我们需要找一个共享内存吧。
"""
