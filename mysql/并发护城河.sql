/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【节点 3.3】：并发护城河 - 悲观锁 (FOR UPDATE) 与 乐观锁 (CAS)

-- 🧠 实用直觉：
-- 假设现在只剩 1 台 iPhone 16，但有 100 个人同时发起购买请求。
--
-- 1. 悲观锁 (Pessimistic Lock): 【总有刁民想抢我的数据，我必须先锁住！】
--    - 做法：我查数据的时候，直接告诉 MySQL“这行数据我征用了，别人全给我等着”。等我扣完库存提交了，下一个人才能查。
--    - 优点：绝对安全，绝不超卖。
--    - 缺点：排队太长，性能极差。并发量太高时，后面的请求会因为等待锁超时 (Lock Wait Timeout) 而全部报错。
--
-- 2. 乐观锁 (Optimistic Lock): 【大家都是好人，先不加锁，最后修改时再检查！】
--    - 做法：我在表里加一个 `version` (版本号) 字段。
--      大家同时查到库存是 1，版本是 0。
--      大家同时去 UPDATE 库存。但语句变成了：`UPDATE ... SET stock = stock - 1, version = version + 1 WHERE id = 1 AND version = 0;`
--      谁的手速快，先执行成功，这行数据的 version 就变成了 1。后面 99 个人再去执行时，因为 `version = 0` 这个条件不成立了，UPDATE 会返回 0 行受影响（意味着抢购失败）。
--    - 优点：不阻塞，吞吐量极高！大厂秒杀必备。
--    - 缺点：会有大量请求失败，需要在 Python/Java 业务层处理失败重试或直接告诉用户“手慢无”。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `SELECT * FROM table WHERE id = ? FOR UPDATE;`
--   注释：悲观锁终极杀器（排他锁 X锁）。必须放在开启的事务 `BEGIN;` 之后使用！
-- - `UPDATE table SET stock = stock-1, version = version+1 WHERE id = ? AND version = ? AND stock > 0;`
--   注释：乐观锁的经典 CAS (Compare And Swap) 语法。利用了单条 SQL 语句本身就是原子操作的特性。

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：为你准备秒杀专用的商品表。
CREATE TABLE IF NOT EXISTS flash_sale_goods (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    goods_name VARCHAR(64) NOT NULL COMMENT '商品名称',
    stock INT UNSIGNED NOT NULL COMMENT '库存',
    version BIGINT UNSIGNED DEFAULT 0 COMMENT '乐观锁版本号'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '高并发秒杀商品表';

TRUNCATE TABLE flash_sale_goods;
-- 初始化：全公司只配发 1 台顶级 GPU 服务器，库存 1，初始版本号为 0
INSERT INTO
    flash_sale_goods (goods_name, stock, version)
VALUES ('NVIDIA H100 Server', 1, 0);

SELECT * FROM flash_sale_goods;
/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误 (会导致严重超卖)】
-- 新手工程师的代码（Python 伪代码）：
-- 1. stock = execute("SELECT stock FROM flash_sale_goods WHERE id = 1;")
-- 2. if stock > 0:
-- 3.     execute("UPDATE flash_sale_goods SET stock = stock - 1 WHERE id = 1;")
-- ❌ 灾难：当并发请求同时执行第一步时，都查到 stock=1。然后他们都绕过了 if 判断，同时执行了第三步，库存瞬间变成负数！

-- 【实战干活：TODO】
-- 背景说明：抢夺这台 'NVIDIA H100 Server'。你需要用原生的 SQL 演示两种防超卖的加锁写法。

-- TODO 1 (悲观锁流派)：使用 `FOR UPDATE` 完成一次安全的库存扣减。
-- 要求：
-- 1. 显式开启事务。
-- 2. 查询 id=1 的库存并加锁。
-- 3. 将库存减 1。
-- 4. 提交事务。
START TRANSACTION;

SELECT stock FROM flash_sale_goods WHERE id = 1 FOR UPDATE;

UPDATE flash_sale_goods SET stock = stock -1 WHERE id = 1;

COMMIT;
-- TODO 2 (乐观锁流派)：假设此时你通过 SELECT 查到当前的 stock 是 1，version 是 0。请使用一条 UPDATE 语句（CAS 机制）尝试扣减库存。
-- 要求：
-- 1. 不需要开启事务。
-- 2. 更新时，库存减 1，version 必须加 1。
-- 3. WHERE 条件里必须包含对当前 version 的检查，并且为了绝对防御，加上 stock > 0 的拦截。
UPDATE flash_sale_goods
SET
    stock = stock - 1,
    version = version + 1
WHERE
    id = 1
    AND version = 0
    and stock > 0;

/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 运行你的 TODO 1 或 TODO 2。
-- 最终验收：SELECT * FROM flash_sale_goods;
-- 结果必须是：stock = 0，如果执行了 TODO 2，version 应该是 1。
SELECT * FROM flash_sale_goods;
/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：死锁 (Deadlock)
-- 老板说悲观锁最安全，于是你满篇都写了 `FOR UPDATE`。
-- 场景：用户 A 想把机器人 ARM-001 和 ARM-002 打包购买。用户 B 刚好想把 ARM-002 和 ARM-001 打包购买。
-- 时间线：
-- [线程 A]: BEGIN; SELECT * FROM goods WHERE id='ARM-001' FOR UPDATE; (成功锁住 001)
-- [线程 B]: BEGIN; SELECT * FROM goods WHERE id='ARM-002' FOR UPDATE; (成功锁住 002)
-- [线程 A]: SELECT * FROM goods WHERE id='ARM-002' FOR UPDATE; (阻塞！等待线程 B 释放 002)
-- [线程 B]: SELECT * FROM goods WHERE id='ARM-001' FOR UPDATE; (阻塞！等待线程 A 释放 001)
--
-- 砰！系统报出 `Deadlock found when trying to get lock`，数据库彻底卡死。

-- 👉 救火任务：
-- "死锁是由于多方互相持有了对方想要的锁，且互不退让造成的。如果在工业界非要用悲观锁（比如复杂的财务结算），为了彻底消灭死锁，我们在 Python/Java 业务层写代码时，对锁的【获取顺序】有一条极其简单的铁律，你知道是什么吗？"
--获取之后最后需要释放，如果不行的话，就设置超时。