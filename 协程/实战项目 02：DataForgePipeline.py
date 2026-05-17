import asyncio
import time
from typing import Any

# ================= 1. 基础设施 (黑盒，你的调用方，禁止修改) =================


# 模拟：从云端拉取一篇原始文章 (耗时，网络 IO)
async def fetch_raw_html(article_id: int) -> str:
    await asyncio.sleep(0.2)  # 网络延迟
    if article_id % 7 == 0:  # 模拟 1/7 的概率拉取失败
        raise ConnectionError(f"Article {article_id} fetch failed!")
    return f"<html><body>Raw content for article {article_id}...</body></html>"


# 模拟：极其耗时的 CPU 密集型清洗算法 (同步代码，千万别卡死循环！)
def heavy_nlp_clean(html_content: str) -> str:
    # time.sleep 模拟 CPU 被霸占
    time.sleep(0.5)
    return html_content.replace("<html><body>", "").replace("</body></html>", "")


# 模拟：异步向量数据库写入
async def save_to_vector_db(article_id: int, clean_text: str) -> None:
    await asyncio.sleep(0.1)  # 磁盘 IO
    # print(f"💾 [DB] 已保存文章 {article_id}")


# ================= 2. 你的架构实战区 (请实现 DataForgePipeline) =================


class DataForgePipeline:
    def __init__(self, queue_maxsize: int = 10, num_consumers: int = 3):
        # 初始化队列容量，防止生产者速度太快撑爆内存
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_maxsize)
        self.num_consumers = num_consumers
        self.stats = {"fetched": 0, "cleaned": 0, "failed": 0}

    async def _producer(self, article_ids: list[int], producer_id: int):
        """
        生产者逻辑：
        1. 遍历分配给自己的 article_ids。
        2. 调用 fetch_raw_html，一定要做异常拦截！失败的记录到 self.stats["failed"]。
        3. 成功的将 (article_id, html_content) 作为一个元组 put 进 self.queue 中。
           记录 self.stats["fetched"] += 1
        """
        print(f"📡 [Producer-{producer_id}] 上线，负责拉取 {len(article_ids)} 篇文章。")
        # TODO: 你的生产者代码
        for article_id in article_ids:
            try:
                html_content = await asyncio.wait_for(
                    fetch_raw_html(article_id), timeout=1
                )
                await self.queue.put((article_id, html_content))
                self.stats["fetched"] += 1
            except ConnectionError, TimeoutError:
                self.stats["failed"] += 1

    async def _consumer(self, consumer_id: int):
        """
        消费者逻辑：
        1. 写一个死循环 while True，不断从 queue.get() 拿任务。
        2. 如果拿到的任务是 None（这就是毒丸！），说明没活了，执行 queue.task_done() 并立刻 break 下班！
        3. 如果是正常数据，调用 to_thread 把 heavy_nlp_clean 扔进后台清洗。
        4. 把清洗好的数据 await save_to_vector_db 存入数据库。
        5. 记录 self.stats["cleaned"] += 1
        6. 必须调用 queue.task_done() 告诉队列这个任务处理完了！
        """
        print(f"⚙️ [Consumer-{consumer_id}] 上线，准备清洗数据。")
        # TODO: 你的消费者代码
        while True:
            result = await self.queue.get()
            if result == None:
                self.queue.task_done()
                break
            data_clean = await asyncio.to_thread(heavy_nlp_clean, result[1])
            await save_to_vector_db(result[0], data_clean)
            self.stats["cleaned"] += 1
            self.queue.task_done()

    async def run(self, total_articles: int):
        """
        流水线总控：
        1. 启动指定数量的 _consumer（挂在后台）。
        2. 把 total_articles 分批（或者一把梭，由你决定），交给几个 _producer 去执行。
           为了简化，你可以只开 1 个 producer 处理所有 total_articles。
        3. await 所有的 producer 执行完毕。
        4. 【灵魂考点】：往队列里投放毒丸（None），数量必须刚好等于消费者的数量，让所有消费者都能拿到解药下班！
        5. await 所有消费者退出。
        """
        print("🚀 DataForge 流水线点火启动...")

        # 构造需要抓取的 ID 列表
        ids_to_fetch = list(range(1, total_articles + 1))

        # TODO: 启动消费者
        consumers = [
            asyncio.create_task(self._consumer(i)) for i in range(self.num_consumers)
        ]

        # TODO: 启动生产者并等待他们全部拉完数据
        producers = []
        for i in range(3):
            chunked_ids = ids_to_fetch[i::3] 
            producers.append(asyncio.create_task(self._producer(chunked_ids, i)))
        await asyncio.gather(*producers, return_exceptions=True)
        # TODO: 投放毒丸让消费者下班，并等待消费者退出
        for _ in range(self.num_consumers):
            await self.queue.put(None)

        await asyncio.gather(*consumers, return_exceptions=True)


# ================= 3. 验收站 =================
def test_crucible():
    print("====== 启动架构师压测 ======")
    # 开 10 容量的队列，3 个消费者
    pipeline = DataForgePipeline(queue_maxsize=10, num_consumers=3)
    start_time = time.time()

    # 压测 15 篇文章
    asyncio.run(pipeline.run(15))

    cost_time = time.time() - start_time
    print("\n📊 流水线最终统计:", pipeline.stats)
    print(f"⏱️ 引擎总耗时: {cost_time:.2f} 秒")

    # 15篇中有两篇 (7和14) 会触发网络异常
    assert pipeline.stats["failed"] == 2, "❌ 失败捕获数量不对！"
    assert pipeline.stats["fetched"] == 13, "❌ 成功拉取数量不对！"
    assert (
        pipeline.stats["cleaned"] == 13
    ), "❌ 清洗入库数量不对！是否有数据在队列里丢失了？或者消费者没做完就强行退出了？"

    # 耗时校验：如果是串行，13 * 0.5 (CPU) = 6.5秒。
    # 3 个消费者并发处理，大概只需 2~3 秒。
    assert cost_time < 3.5, "❌ 耗时过长！你是不是卡死了主事件循环？"

    print("✅ 完美的流水线！生产者与消费者完美解耦，优雅停机测试通过！")


if __name__ == "__main__":
    test_crucible()
