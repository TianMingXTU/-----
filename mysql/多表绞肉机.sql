-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【合并节点 1.1 ~ 1.3】：多表绞肉机 - 连表与嵌套的艺术

-- 🧠 实用直觉：
-- 1. 笛卡尔积 (The Disaster)：如果你写 `SELECT * FROM A, B` 且不加条件，A表 1000条，B表 1000条，数据库会直接吐出 100 万条数据，瞬间把你内存撑爆。所有的 JOIN，本质上都是在消除无意义的笛卡尔积。
-- 2. 内连接 (INNER JOIN)：【找交集】。“查出那些【既在】A表【又有】维修记录的数据”。两边匹配不上的，直接丢弃。
-- 3. 左外连接 (LEFT JOIN)：【主从分明】。以左边的表为基准（全要），去右边找匹配。右边没有对应的？那就补 NULL。老板说“给我所有机器人的名单，如果有维修记录就带上，没有就算了”，无脑选 LEFT JOIN。
-- 4. 子查询 (Subquery - IN / EXISTS)：【嵌套逻辑】。先在子查询里查出一个集合，再作为外层查询的条件。
--    - 小表驱动：子查询结果集很小（比如就查几十个 ID），用 `IN`。
--    - 大表驱动：子查询结果集巨大，用 `EXISTS`（利用索引快速探测是否存在，而不是全部查出来）。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `FROM A INNER JOIN B ON A.key = B.key`
--   注释：标准内连接语法。不要用老掉牙的 `WHERE A.key = B.key` 来代替 JOIN，语义不清晰。
-- - `FROM A LEFT JOIN B ON A.key = B.key`
--   注释：左外连接。永远记住，把你想要【确保数据完整不丢失】的那张表放在 LEFT JOIN 的左边（称为“驱动表”）。
-- - `WHERE A.id IN (SELECT b_id FROM B WHERE condition)`
--   注释：子查询。直观，但极易踩坑引发全表扫描。

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：建立关联表 `repair_logs` (维修记录)，并写入测试数据。
-- (直接复制执行即可)
CREATE TABLE IF NOT EXISTS repair_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    robot_sn VARCHAR(64) NOT NULL COMMENT '机器人序列号(逻辑外键)',
    repair_reason VARCHAR(255) COMMENT '维修原因',
    cost DECIMAL(8, 2) COMMENT '维修花费',
    INDEX idx_robot_sn (robot_sn) -- 👈 上一节课血的教训：逻辑外键必须加普通索引！
) COMMENT = '机器人维修记录表';

TRUNCATE TABLE repair_logs;
-- ARM-101 修了两次，ARM-201 修了一次，其他机器没修过
INSERT INTO
    repair_logs (robot_sn, repair_reason, cost)
VALUES ('ARM-101', '履带卡死', 500.00),
    ('ARM-101', '主板进水', 2000.00),
    ('ARM-201', '传感器失灵', 350.00);

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 实习生想看机器人的维修账单，写出了：
-- SELECT * FROM robots LEFT JOIN repair_logs ON robots.id = repair_logs.id;
-- ❌ 灾难：连表字段（Join Key）完全选错了！机器人的主键 `id` 怎么能和维修记录的主键 `id` 去匹配？张冠李戴，查出来全是错乱的数据！必须用逻辑外键关联。

-- 【实战干活：TODO】
-- 背景说明：售后维修部和财务部找你要报表数据。
-- 你的表结构回顾：`robots` (id, robot_sn, status, firmware_version) | `repair_logs` (id, robot_sn, repair_reason, cost)

-- 实战要求 1 (INNER JOIN)：财务部要核对账单。请查出【发生过维修】的机器人的 SN 号、状态 (status) 以及每次维修的原因 (repair_reason) 和花费 (cost)。
-- TODO 1: 编写你的 INNER JOIN 语句...
SELECT robots.robot_sn, robots.status, repair_logs.repair_reason, repair_logs.cost
FROM robots
    INNER JOIN repair_logs ON robots.robot_sn = repair_logs.robot_sn;
-- 实战要求 2 (LEFT JOIN)：售后部要盘点所有机器。请查出【所有】机器人的 SN 号、状态。如果它修过，展示它的维修原因；如果没修过，对应的原因必须显示为 NULL。（提示：谁是驱动表？）
-- TODO 2: 编写你的 LEFT JOIN 语句...
SELECT robots.robot_sn, robots.status, repair_logs.repair_reason
FROM robots
    LEFT JOIN repair_logs ON robots.robot_sn = repair_logs.robot_sn;
-- 实战要求 3 (Subquery / NOT IN)：运营部发现有机器状态异常。请利用【子查询 (IN / NOT IN)】，查出：状态为 0 (离线闲置)，且【从来没有出现在 repair_logs 表中】的机器人 SN 号。（排查是不是坏了没人修）。
-- TODO 3: 编写你的子查询语句...
SELECT *
FROM robots
WHERE
    status = 0
    AND robot_sn NOT IN(
        SELECT robot_sn
        FROM repair_logs
    );
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 运行你的三个 TODO。
-- 验收 TODO 1：结果应有 3 条记录（ARM-101占两条，ARM-201占一条）。没修过的机器不该出现。
-- 验收 TODO 2：结果应有 10 条记录（因为 ARM-101 有两条记录，其他机器人各一条，没修过的全带 NULL）。
-- 验收 TODO 3：结果应查出 ARM-202, ARM-203, ARM-204（它们 status 是 0，且在 repair_logs 里找不到 SN）。

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 你用 `LEFT JOIN` 写了一个极其复杂的报表查询，关联了 `orders` (订单表，1000万数据) 和 `users` (用户表，500万数据)。
-- 你的 SQL 是这样的：`SELECT * FROM orders LEFT JOIN users ON orders.buyer_name = users.username;`
-- 这个 SQL 发到线上后，数据库实例直接 OOM (Out of Memory) 宕机，并拉爆了整个机房的磁盘 IO。

-- 👉 救火任务：
-- "不用看执行计划（EXPLAIN），凭借直觉告诉我，为什么这个连表操作会引发核爆级灾难？在 MySQL 底层的连表算法 (Nested-Loop Join) 中，
--如果没有在被驱动表 (users) 的连表字段 (`username`) 上建索引，MySQL 是怎么执行这种连表的？（提示：算一下大O复杂度）"
/*
我觉得应该是将1000万数据都加载到内存里面了，建立索引的话是以时间换空间，大O是O(n)。
*/