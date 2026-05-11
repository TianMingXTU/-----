# ================= 0. 知识点讲解 =================
"""
【代理式共享陷阱 (Manager)】

直觉模型：
前面的 `Value` 和 `Array` 只能共享简单的 C 语言类型（int, float）。
如果你想在多个进程间共享复杂的 Python 对象（比如 `dict`, `list`），你需要请一个“大管家”—— `multiprocessing.Manager()`。
管家会在后台启动一个完全独立的“服务器进程”来集中保管这些数据，其他子进程拿到的是“代理凭证 (Proxy)”。
子进程每次读写字典，都是在跟管家进行跨进程通信（IPC）。

致命陷阱：
1. 性能深渊：因为每次读写都要经过底层 Socket 通信、获取管家锁、序列化、反序列化，千万不要在千万级的 `for` 循环里直接操作 Manager 对象！
2. 嵌套更新盲区 (Nested Mutation Trap)：这是无数高级开发踩过的大坑！
   如果你有一个管家字典 `d = manager.dict()`，里面存了一个普通列表 `d['records'] = []`。
   子进程执行 `d['records'].append('A')` 时，管家**根本不知道**内部的普通列表被修改了！数据直接丢失！
   - 破解招式：必须【重新赋值】触发管家字典的 `__setitem__` 拦截器。
     `temp = d['records']`   # 先拿出来
     `temp.append('A')`      # 在内存里修改
     `d['records'] = temp`   # 强行塞回去，触发更新
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time

# ================= 2. 代码骨架 (Starter Code) =================


def naive_worker(worker_id, shared_dict, lock):
    """
    【业务场景】每个工人往共享的字典中的列表中，添加自己的打卡记录。
    （注：多个进程同时修改同一个共享资源，为了防止写冲突，依然需要加锁防踩踏）
    """
    with lock:
        # 💣 陷阱原貌：直接修改嵌套在代理对象内部的普通列表。管家毫无察觉，数据必定丢失！
        # shared_dict['logs'].append(f"Worker-{worker_id} 打卡")

        # TODO 1: 请修复上面的代码，用“提取 -> 修改 -> 重新赋值”的连招，强行通知管家更新。
        temp = shared_dict["logs"]
        temp.append(f"Worker-{worker_id} 打卡")
        shared_dict["logs"] = temp


def manager_engine():
    """
    TODO 2: 在此配置 Manager 和并发逻辑
    """
    # 1. 聘请大管家 (必须用 with 语句保证管家进程最后能正常关闭释放资源)
    with multiprocessing.Manager() as manager:

        # 2. 让管家创建一个共享字典，和一把管家锁
        shared_dict = manager.dict()
        lock = multiprocessing.Lock()

        # 3. 初始化嵌套列表 (注意，字典是代理的，但里面的 [] 是一个普通 Python 列表)
        shared_dict["logs"] = []

        # 4. 创建 3 个子进程，分别执行 naive_worker
        p_list = []
        for i in range(3):
            p = multiprocessing.Process(
                target=naive_worker, args=(i, shared_dict, lock)
            )
            p.start()
            p_list.append(p)

        for p in p_list:
            p.join()

        # 5. 返回最终的字典内容 (用 dict() 将其从代理对象转回普通字典，否则出了 with 作用域就销毁了)
        return dict(shared_dict)


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    start_time = time.time()
    final_result = manager_engine()
    total_cost = time.time() - start_time

    if final_result is None or "logs" not in final_result:
        raise AssertionError("❌ 灾难级 Bug：你没有返回正确的字典结构。")

    logs = final_result["logs"]
    print(f"📊 最终收集到的打卡记录: {logs}")

    if len(logs) != 3:
        raise AssertionError(
            f"❌ 嵌套更新盲区：管家丢数据了！期望 3 条记录，实际只有 {len(logs)} 条。你一定是没有重新赋值！"
        )

    print("✅ All Tests Passed! 恭喜 AC！你避开了 Manager 最可怕的嵌套修改陷阱。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
既然 Manager 这么强大，能共享复杂的 dict 和 list，为什么我们不在所有的地方都用 Manager 替代之前学的 Queue 和 Pipe？
试从“底层通信开销 (IPC)”和“中心化锁竞争”的角度，推演一下如果在高并发的场景下，让 10 个进程疯狂向同一个 Manager dict 里各写入 100 万条数据，系统会遭遇什么性能瓶颈？
（提示：想想管家是不是只有一个人？他每次接客是不是都要全套服务？）
回答：管家只有一个人，每次接客是都要全套服务，总体而言，Manager太慢了。
"""
