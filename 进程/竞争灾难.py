"""
在这个挑战中，我们将制造一场极其混乱的“踩踏事故”。
你需要创建 10 个子进程，每个子进程都像疯子一样，
对这块公共黑板上的数字进行 10万次 的 +1 操作。
"""

# ================= 1. 依赖导入 =================
import multiprocessing
import time


# ================= 2. 反骨破坏任务 =================
def rebel_worker(shared_counter):
    """
    反骨仔的破坏任务：疯狂给共享变量加 1，执行 100,000 次。
    """
    for _ in range(100000):
        # TODO 1: 怎么对共享变量的值加 1？
        # 注意：不能直接写 shared_counter += 1，想一想上面提到的属性。
        shared_counter.value += 1


# ================= 3. 刻意练习骨架 =================
def main():
    # 召唤公共黑板：申请一块 C 语言级别的共享内存（整数类型，初始为0）
    shared_counter = multiprocessing.Value("i", 0)

    print("[主进程] 释放 10 个反骨子进程，准备造成混乱...")

    # 用来装这 10 个子进程对象的列表
    processes = []

    # TODO 2: 循环 10 次，每次实例化一个 Process，目标是 rebel_worker。
    # 记得把 shared_counter 作为参数 (args) 传给它，然后 start() 点火，并追加到 processes 列表中。
    for i in range(10):
        p = multiprocessing.Process(target=rebel_worker, args=(shared_counter,))
        p.start()
        processes.append(p)

    # TODO 3: 循环遍历 processes 列表，把所有的子进程 join() 阻塞住，确保它们都执行完。
    # 如果不 join，主进程会直接跑到底，你拿到的结果可能就是 0。
    for p in processes:
        p.join()

    # 终极见证时刻：
    print(f"[主进程] 所有子进程厮杀完毕！")
    print(f"[主进程] 理论上的完美结果应该是: 1000000")
    print(f"[主进程] 反骨仔实际跑出来的结果是: {shared_counter.value}")


if __name__ == "__main__":
    main()
