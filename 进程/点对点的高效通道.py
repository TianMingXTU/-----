# ================= 0. 知识点讲解 =================
"""
【点对点的高效通道 (Pipe)】

直觉模型：
如果说 Queue（队列）是车间里的“公共传送带”，大家都可以往上扔、大家都可以拿（自带复杂的防踩踏锁）；
那么 Pipe（管道）就是两个特工之间的“私人加密对讲机”。它更底层、更轻量，速度也更快。

核心区别与陷阱：
1. 双向通讯 (Duplex)：默认情况下，Pipe 是双向的。对讲机有两端，特工 A 拿一端，特工 B 拿一端，两人都可以说 (send) 和听 (recv)。
2. 绝对的点对点：一根 Pipe 只能有两个端点！千万不要让三个进程去抢同一个 Pipe 的端点，由于没有 Queue 那种防踩踏机制，数据会瞬间错乱崩溃。
3. 阻塞与断开：如果你去听 (recv)，但对方一直没说话，你会一直等。如果对方把他的对讲机砸了（调用了 `close()`），你去听的时候系统会直接抛出 `EOFError`（End Of File）。

核心语法：
- 申请对讲机：conn1, conn2 = multiprocessing.Pipe()
- 说话：conn.send(数据)
- 听话：data = conn.recv()
- 挂断：conn.close()
"""

# ================= 1. 依赖导入 (Imports) =================
import multiprocessing
import time

# ================= 2. 代码骨架 (Starter Code) =================


def ping_agent(conn, rounds):
    """
    特工 Ping (发球方)：
    他负责先发球 (Ping)，然后等待对方打回来的球 (Pong)。
    """
    for i in range(rounds):
        # 1. 发球
        msg_out = f"Ping-{i}"
        print(f"[Ping特工] 发送: {msg_out}")
        conn.send(msg_out)

        # 2. 等待接球
        # TODO 1: 阻塞接收对方发来的消息，并存入 msg_in
        msg_in = conn.recv()
        print(f"[Ping特工] 收到回击: {msg_in}")
        time.sleep(0.05)

    # TODO 2: 打完了，挂断对讲机 (关闭连接)
    conn.close()


def pong_agent(conn):
    """
    特工 Pong (接球方)：
    他不知道要打多少回合，他的逻辑是：只要一直能收到球，就回击。如果对方挂断了，他就撤退。
    """
    while True:
        try:
            # TODO 3: 接收对方发来的消息
            msg_in = conn.recv()
            print(f"      [Pong特工] 截获: {msg_in}，准备反击...")

            # TODO 4: 把收到的消息前面的 "Ping" 替换成 "Pong"，然后发送回去
            msg_out = msg_in.replace("Ping", "Pong")
            conn.send(msg_out)

        except EOFError:
            # TODO 5: 捕获到对讲机断开异常，打印撤退信息并退出循环
            print("      [Pong特工] 听见对面挂断了 (EOFError)，任务结束，撤退！")
            break


def pipe_game(rounds):
    """
    TODO: 在此实现你们的点对点双向通信引擎
    """
    # 1. 申请对讲机 (创建 Pipe)
    conn1, conn2 = multiprocessing.Pipe()
    # 2. 招募两个特工 (创建进程)
    # 把 conn1 给 ping_agent，把 conn2 给 pong_agent
    p_ping = multiprocessing.Process(target=ping_agent, args=(conn1, rounds))
    p_pong = multiprocessing.Process(target=pong_agent, args=(conn2,))

    # 3. 启动并等待任务结束
    p_ping.start()
    p_pong.start()

    conn1.close()
    conn2.close()

    p_ping.join()
    p_pong.join()


# ================= 3. 黑盒测试 (Test Cases) =================
def test_crucible():
    print("--- 🚀 开始执行工业级黑盒测试 ---")

    # 理论上应该能够顺利打完 5 个回合的 Ping-Pong，并且没有任何死锁，最后抛出 EOFError 正常退出。
    start_time = time.time()
    pipe_game(5)
    cost = time.time() - start_time

    if cost > 2.0:
        raise AssertionError(
            "❌ 灾难级 Bug：耗时过长！是不是有人在死等（死锁了）？检查你的 close() 和 EOFError 逻辑！"
        )
    elif cost < 0.2:
        raise AssertionError("❌ 逻辑异常：太快了，回合肯定没打完就退出了。")

    print("✅ All Tests Passed! 恭喜 AC！你成功建立了底层的高速对讲网络。")


if __name__ == "__main__":
    test_crucible()

# ================= 4. 慢思考 =================
"""
🧠 慢思考拷问：
在工业生产中，如果你要传递非常巨大的数据（比如一个 10MB 的高清图片二进制流），
使用 `multiprocessing.Queue` 和 `multiprocessing.Pipe` 哪个性能更好？为什么？
（提示：想想 Queue 为了保证多进程安全，底层悄悄加上了什么“沉重”的防御装备？）
回答：使用Pipe更好，因为它没得锁，而且还是点对点传输
"""
