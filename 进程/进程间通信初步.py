# ================= 0. 知识点讲解 =================
"""
【进程间通信 (IPC) - 队列 Queue】

直觉模型：既然多进程的内存是物理隔离的（像两家完全独立的餐厅），那他们怎么传递食材？
答案是修一条双向的“安全传送带”。multiprocessing.Queue 就是这条传送带。
最棒的是，它底层自动帮你加好锁了（自带防踩踏机制），你不需要手动去 acquire/release，多进程读写绝对安全。

核心语法：
- 打造传送带：q = multiprocessing.Queue()
- 生产者放东西：q.put(数据)
- 消费者拿东西：q.get()

⚠️ 致命陷阱提示（死锁幽灵）：
如果传送带上空了，消费者调用 q.get() 时不会报错，而是会**一直原地死等（阻塞）**，直到有新东西放上来。
所以，生产者下班前，必须在传送带上放一个“特殊信号”（行业俗称 Poison Pill 毒药/停止符，通常是 None），告诉消费者：“别等了，关门了”。
"""

# ================= 1. 依赖导入 =================
import multiprocessing
import time
import os


# ================= 2. 生产者与消费者任务 =================
def producer(queue):
    """生产者：负责做包子，放到传送带上"""
    for i in range(1, 6):
        baozi = f"肉包子-{i}号"
        print(f"[生产者] 做了 {baozi}，放到传送带上。")

        # TODO 1: 把 baozi 放进队列中
        queue.put(baozi)

        time.sleep(0.5)  # 做包子比较快：0.5秒做一个

    # 包子做完了，放一个特殊的信号（停止符 None）告诉消费者下班
    print(f"[生产者] 5个包子做完了，收工！放一个 None 告诉消费者没货了。")
    queue.put(None)


def consumer(queue):
    """消费者：负责从传送带上拿包子吃"""
    while True:
        # TODO 2: 从队列中拿取包子
        # baozi = ...
        baozi = queue.get()
        # 检查是不是下班信号
        if baozi is None:
            print(f"[消费者]{os.getpid()} 拿到下班信号(None)，撑死了，下班！")
            break

        print(f"      [消费者]{os.getpid()} 从传送带上拿到并吃掉: {baozi}")
        time.sleep(1)  # 吃包子比较慢：1秒吃一个


# ================= 3. 餐厅主进程骨架 =================
def main():
    print("[主进程] 餐厅开业！打造传送带...")

    # TODO 3: 实例化一个多进程安全的队列
    my_queue = multiprocessing.Queue(3)
    # TODO 4: 实例化两个进程：一个执行 producer，一个执行 consumer。
    # ❗️极度重要：记得把 my_queue 作为参数 (args) 传给它们！否则他们连不上同一个传送带。
    p_producer = multiprocessing.Process(target=producer, args=(my_queue,))
    p_consumer_1 = multiprocessing.Process(target=consumer, args=(my_queue,))
    p_consumer_2 = multiprocessing.Process(target=consumer, args=(my_queue,))
    p_consumer_3 = multiprocessing.Process(target=consumer, args=(my_queue,))
    # 点火启动
    p_producer.start()
    p_consumer_1.start()
    p_consumer_2.start()
    p_consumer_3.start()

    # 阻塞等待他们下班
    p_producer.join()
    p_consumer_1.join()
    p_consumer_2.join()
    p_consumer_3.join()

    print("[主进程] 一天营业结束，关门大吉！")


if __name__ == "__main__":
    main()
# ================= 4. 慢思考 =================
"""
问题：
观察运行时间你会发现，做包子很快（0.5秒），吃包子很慢（1秒）。
如果我在主进程里开 1 个生产者进程，却开了 3 个消费者进程（3 个人抢包子吃）。
此时，生产者最后只发了 1 个 None 信号。请问这 3 个消费者都能正常下班吗？如果不能，会发生什么恐怖的事情？要怎么解决？
回答：
 3 个消费者只有一个会拿到None，其他两个线程就会卡死，解决方案是，根据消费者数量生成None或者是采用拿到None之后不要put
"""
