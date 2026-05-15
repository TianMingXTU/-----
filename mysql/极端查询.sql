/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【合并节点 4.1 ~ 4.2】：极端查询 - 千万级深分页与复杂报表降维打击

-- 🧠 实用直觉：
-- 1. 深分页 (Deep Pagination) 的灾难：
--    - 现象：前端传参数 `page=100000, size=10`。你写出 `LIMIT 1000000, 10`。
--    - 底层真相：MySQL 并不是直接跳到第 100 万行。它是把前面的 100 万零 10 行数据**全部查出来**，然后扔掉前 100 万行，只给你返回最后 10 行！这叫“回表”爆炸，查询时间会从 10 毫秒飙升到 10 秒甚至超时。
--    - 工业级解法 A (游标法 / 瀑布流)：记住上一页最后一条的 ID，直接 `WHERE id > last_id LIMIT 10`。速度永远是 O(1)。
--    - 工业级解法 B (子查询延迟关联)：如果非要跳页，先用覆盖索引只查出那 10 条的 ID，然后再去 JOIN 原表拿完整数据。
--
-- 2. 窗口函数 (Window Functions, MySQL 8.0+)：
--    - 痛点：老板要求“查出每个大区销量排名前 3 的机器人”。在 MySQL 5.7 时代，这需要极其恶心的自连接和 GROUP BY 嵌套，代码能写几十行。
--    - 降维打击：在原表基础上开一扇“窗”，对数据进行**分组（PARTITION BY）**和**排序（ORDER BY）**，但不合并行（不同于 GROUP BY）。直接算出名次！

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `SELECT * FROM t INNER JOIN (SELECT id FROM t LIMIT 1000000, 10) AS tmp ON t.id = tmp.id;`
--   注释：深分页救火术（延迟关联）。括号里的子查询只查主键，走“覆盖索引”，速度极快；然后再用这 10 个 ID 去 JOIN 原表，最多只回表 10 次！
-- - `ROW_NUMBER() OVER (PARTITION BY region ORDER BY score DESC)`
--   注释：窗口函数。给数据按 region 分组，每组按 score 降序，并打上 1, 2, 3... 的连续排名序号。

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：为你准备两张千万级体量（概念上）的表。
CREATE TABLE IF NOT EXISTS robot_operation_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    robot_sn VARCHAR(64) NOT NULL,
    action_detail VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_at (created_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '机器人操作日志(模拟千万级)';

CREATE TABLE IF NOT EXISTS robot_sales_performance (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(32) NOT NULL COMMENT '大区',
    robot_model VARCHAR(32) NOT NULL COMMENT '机型',
    sales_amount DECIMAL(10, 2) NOT NULL COMMENT '销售额'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

TRUNCATE TABLE robot_sales_performance;

INSERT INTO
    robot_sales_performance (
        region,
        robot_model,
        sales_amount
    )
VALUES ('华北区', 'ARM-100', 50000),
    ('华北区', 'ARM-200', 80000),
    ('华北区', 'ARM-300', 45000),
    ('华北区', 'ARM-400', 90000),
    ('华南区', 'ARM-100', 60000),
    ('华南区', 'ARM-200', 70000),
    ('华南区', 'ARM-300', 75000),
    ('华南区', 'ARM-400', 30000);

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 运营后台需要查看历史操作日志，直接翻到了第 10 万页。
-- 实习生写的 SQL：SELECT * FROM robot_operation_logs ORDER BY created_at DESC LIMIT 1000000, 20;
-- ❌ 灾难：`SELECT *` 导致了严重的“回表”。按时间排序扫了 100 万行，回表 100 万次，数据库 CPU 直接打满 100%，系统告警。

-- 【实战干活：TODO】

-- TODO 1 (深分页救火)：请使用【子查询延迟关联】的方法，重写实习生的这句 SQL。
-- 目标：只取第 1000000 开始的 20 条数据，按 created_at 降序。但必须干掉那前 100 万次的无意义回表！
-- 提示：先查 ID！
SELECT r.*
FROM
    robot_operation_logs r
    INNER JOIN (
        SELECT *
        FROM robot_operation_logs
        ORDER BY id
        LIMIT 1000000, 20
    ) as tmp ON r.id = tmp.id;
-- TODO 2 (降维打击)：老板发话了：“给我查出【每个大区 (region)】里，销售额 (sales_amount) 排在【前 2 名】的机型和销售额。”
-- 目标：使用 MySQL 8.0 的窗口函数 `ROW_NUMBER()` 实现。
-- 提示：
-- 第一步：写个内层查询，用 ROW_NUMBER() 给每一行打上排名标号（取个别名叫 rnk）。
-- 第二步：在外面套一层 SELECT，加上 WHERE rnk <= 2。

SELECT *
FROM (
        SELECT region, sales_amount, ROW_NUMBER() OVER (
                PARTITION BY
                    region
                ORDER BY sales_amount DESC
            ) as rnk
        FROM robot_sales_performance
    ) AS ranked_data
WHERE
    rnk <= 2;
-- 只取每组的前三名

/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 验收 TODO 2：
-- 结果必须只有 4 行：
-- 华北区 | ARM-400 | 90000
-- 华北区 | ARM-200 | 80000
-- 华南区 | ARM-300 | 75000
-- 华南区 | ARM-200 | 70000

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 就算你用了子查询延迟关联（`INNER JOIN (SELECT id FROM ... LIMIT 1000000, 20)`），当 OFFSET 达到了 5000 万级别时，子查询本身扫那 5000 万个 ID 依然会耗时数秒。
-- 你的架构师眉头一皱，对你说：“对于 App 的信息流或者日志流水，用户根本不需要精确地‘跳到第 15432 页’，他们只会一直往下滑动加载。”

-- 👉 救火任务：
-- "如果在产品交互上，我们把底部的【跳页组件（1, 2, 3... 100）】改成【下拉加载更多 (Load More)】。
-- 你的 SQL 应该发生怎样翻天覆地的变化？请写出这种被称为‘游标法’或‘瀑布流’的极其优雅的 SQL 骨架。它的时间复杂度为什么能永远保持在 O(1)？"
-- 记住上一页最后一条的 ID，直接 `WHERE id > last_id LIMIT 10`。速度永远是 O(1)