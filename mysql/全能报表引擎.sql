-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【合并节点 0.5 ~ 0.8】：全能报表引擎 - 过滤、转换、聚合与分页 (DQL)

-- 🧠 实用直觉：
-- 把 SQL 查询当成一条极其严密的“数据流水线”（Pipeline），它有绝对的执行顺序：
-- 1. FROM/JOIN: 先确定去哪个仓库找数据。
-- 2. WHERE (节点0.5): 在仓库门口设卡，把不符合条件的垃圾数据直接拦在门外。（注意：这里不能用聚合函数）
-- 3. GROUP BY (节点0.8): 把进门的数据按某个特征（比如状态、部门）分堆。
-- 4. SELECT & 函数 (节点0.6/0.7): 对每堆数据进行计算（COUNT/SUM）和包装（CASE WHEN 翻译状态码，DATE_FORMAT 格式化时间）。
-- 5. HAVING (节点0.8): 对“分堆计算后”的结果再次设卡过滤（比如：只保留数量大于 10 的堆）。
-- 6. ORDER BY (节点0.5): 对最终结果排序。
-- 7. LIMIT (节点0.5): 截取前 N 条，打包发给前端。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `CASE WHEN condition THEN 'A' ELSE 'B' END`
--   注释：SQL 里的 if-else 分支。用于把数据库里的魔法数字（0, 1, -1）翻译成前端人类能看懂的文字（离线, 在线, 报废）。
-- - `DATE(created_at)` / `DATE_FORMAT(created_at, '%Y-%m-%d')`
--   注释：时间降维打击。把精确到秒的时间截断到“天”，常用于按天统计日活。
-- - `COUNT(1)` vs `COUNT(column)`
--   注释：工业界统计行数无脑用 `COUNT(1)` 或 `COUNT(*)`，不要写具体字段名（除非你想故意忽略 NULL 值）。
-- - `GROUP BY column_name`
--   注释：聚合的灵魂。记住一条铁律：SELECT 里除了聚合函数（COUNT/SUM/MAX）之外的普通字段，**必须**出现在 GROUP BY 里！

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：为了让你能测试复杂的聚合查询，先执行以下语句，给你造一点模拟数据！
-- (直接复制执行即可)
TRUNCATE TABLE robots;

INSERT INTO
    robots (
        robot_sn,
        status,
        firmware_version
    )
VALUES ('ARM-101', 1, 'v3.0'),
    ('ARM-102', 1, 'v3.0'),
    ('ARM-103', 1, 'v3.1'),
    ('ARM-201', 0, 'v2.0'),
    ('ARM-202', 0, 'v2.0'),
    ('ARM-203', 0, NULL),
    ('ARM-204', 0, NULL),
    ('ARM-998', -1, 'v1.0'),
    ('ARM-999', -1, 'v1.0');

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 老板要统计“各个状态的机器人有多少台”。
-- 新手的致命写法：
-- SELECT status, COUNT(1) FROM robots; -- ❌ 报错：你用了 COUNT，但没有用 GROUP BY，数据库不知道你是要算总数还是按 status 分组。
-- SELECT * FROM robots GROUP BY status; -- ❌ 灾难：在 MySQL 8.0 严格模式下直接报错（ONLY_FULL_GROUP_BY）。你按状态分组了，那每组里那么多条数据，你 SELECT * 到底展示哪一条？

-- 【实战干活：TODO】
-- 背景说明：运营总监需要一个“机器人大盘统计看板”的 API 数据源。
-- 实战要求（必须用一条 SQL 搞定）：
-- 1. 过滤：他不想看到 `firmware_version` 为 NULL 的机器（用 WHERE 剔除）。
-- 2. 分组与统计：按机器人的 `status`（状态）进行分组，统计每种状态下有多少台机器（使用 COUNT）。
-- 3. 数据翻译（难点）：在 SELECT 结果中，不要返回 1, 0, -1，而是使用 `CASE WHEN` 翻译成一个新字段 `status_text`，对应关系为：1 -> '在线正常', 0 -> '离线闲置', -1 -> '已报废', 其他 -> '未知状态'。
-- 4. 排序：按照统计出来的数量 (`robot_count`) 从大到小降序排列 (DESC)。
-- 5. 分页：假设后续会有很多状态，前端要求只取数量排名前 2 的状态类别 (LIMIT)。

-- TODO: 编写这条终极报表 SQL 引擎语句
-- 期望输出的字段名必须是：`status_text`, `robot_count`
-- 你的 SQL 写在这里...
SELECT * FROM robots;

SELECT * FROM robots WHERE firmware_version is NOT NULL;

SELECT status, COUNT(1) FROM robots GROUP BY status;

SELECT
    CASE
        WHEN status = 1 THEN "在线正常"
        WHEN status = 0 THEN "离线闲置"
        WHEN status = -1 THEN "已报废"
        ELSE "未知状态"
    END as "status_text",
    COUNT(*) as num
FROM robots
GROUP BY
    status;

SELECT
    CASE
        WHEN status = 1 THEN "在线正常"
        WHEN status = 0 THEN "离线闲置"
        WHEN status = -1 THEN "已报废"
        ELSE "未知状态"
    END as "status_text",
    COUNT(*) as num
FROM robots
GROUP BY
    status
ORDER BY num DESC;

SELECT
    CASE
        WHEN status = 1 THEN "在线正常"
        WHEN status = 0 THEN "离线闲置"
        WHEN status = -1 THEN "已报废"
        ELSE "未知状态"
    END as "status_text",
    COUNT(*) as num
FROM robots
WHERE
    firmware_version IS NOT NULL
GROUP BY
    status
ORDER BY num DESC
LIMIT 2;
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 运行你的 TODO SQL。
-- 打印："✅ 验收标准：结果必须只有 2 行。第一行是 '在线正常' (3台)，第二行是 '离线闲置' (2台)。'已报废' 的数据应该排在第三被 LIMIT 截掉，没有固件版本的废弃数据应该在 WHERE 阶段被扔掉了。准备下班。"

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 你用 `GROUP BY status` 完美写出了看板接口。半年后，`robots` 表膨胀到了 5000 万条记录。
-- 老板某天早上一打开看板，页面疯狂转圈，最后报了 504 Gateway Timeout。你一看监控，数据库 CPU 飙到了 100%。DBA 怒气冲冲地跑过来：“你的 GROUP BY 查出了 `Using temporary; Using filesort`，把内存给干爆了！”

-- 👉 救火任务：
-- "不用管 Python 代码，只在数据库层面看。为什么对 5000 万数据的字段直接 GROUP BY 会产生可怕的临时表（temporary table）和文件排序（filesort）？要彻底解决这个报表查询导致 CPU 打满的问题，你唯一且必须要做的一个物理层动作是什么？（提示：回顾一下战区零前几关学过的东西）"
/*
因为锁的机制，GROUP BY不能直接修改原来的表，只能创建临时表进行排序。解决方法我不是很清楚。
*/