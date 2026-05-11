# ================= 0.知识点讲解 =================
"""
面对混乱的踩踏，操作系统提供了一种终极暴力镇压工具：互斥锁 (Mutex / Lock)。

直觉模型：想象这个公共黑板前，现在只放了一支笔。如果你想改黑板，你必须先抢到这支笔（acquire）。
如果你没抢到，你就只能在旁边死等（阻塞挂起），直到拿着笔的人写完，把笔放下（release）。

核心语法：lock = multiprocessing.Lock()。
"""

# ================= 1. 依赖导入 =================
import multiprocessing


# ================= 2. 戴上镣铐的任务 =================
def disciplined_worker(shared_counter, lock):
    """
    被收编的反骨仔：现在每次修改黑板前，必须先抢到唯一的锁。
    """
    for _ in range(100000):
        # TODO 1: 抢夺锁。抢不到就给我原地等着！
        # ...

        # 只有抢到锁，才能执行神圣的非原子操作
        with lock:
            shared_counter.value += 1

        # TODO 2: 写完了，把锁释放掉，让别人抢！
        # ...


# ================= 3. 典狱长骨架 =================
def main():
    shared_counter = multiprocessing.Value("i", 0)
    # TODO 3: 打造一把独一无二的进程锁
    # my_lock = ...
    my_lock = multiprocessing.Lock()

    print("[主进程] 典狱长下达指令，带锁的反骨仔们开始干活...")
    processes = []

    for i in range(10):
        # TODO 4: 实例化进程时，除了传 counter，还要把锁传给他们
        p = multiprocessing.Process(
            target=disciplined_worker,
            args=(shared_counter, my_lock),
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # 终极见证时刻：
    print(f"[主进程] 厮杀完毕！")
    print(
        f"[主进程] 加锁后的最终结果是: {shared_counter.value} （如果是 1000000，说明镇压成功！）"
    )


if __name__ == "__main__":
    main()
