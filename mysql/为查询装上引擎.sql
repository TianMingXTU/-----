-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【合并节点 2.1 ~ 2.3】：为查询装上引擎 (Indexes & EXPLAIN)

-- 🧠 实用直觉：
-- 1. B+ 树黑盒：MySQL 的 InnoDB 引擎里，数据不是乱放的，全在一棵树上（聚簇索引，主键做 Key，叶子存整行数据）。
-- 2. 二级索引 (Secondary Index)：你自己建的索引，是一棵“新树”。这棵树的叶子节点【不存整行数据，只存主键 ID】。
-- 3. 回表 (The Bottleneck)：如果你用二级索引查数据，但 SELECT 了索引树里没有的字段，MySQL 只能拿着主键 ID 去主树（聚簇索引）里再查一次。这叫“回表”。高并发下，回表极其消耗磁盘 IO。
-- 4. 覆盖索引 (Covering Index / 干掉回表)：最高级的优化手段。你 SELECT 的字段，刚好都在二级索引树里，直接从索引树返回结果，不用去主树！速度快到飞起。
-- 5. 最左前缀法则 (Leftmost Prefix)：对于联合索引 `(A, B, C)`，相当于先按 A 排序，A 相同按 B 排... 你的 WHERE 条件必须从最左边开始用。你可以查 A，查 AB，查 ABC。但如果你直接 WHERE B=1，或者 WHERE A=1 AND C=1（C会失效），这棵树你就用不上了。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `CREATE INDEX idx_name ON table_name (col1, col2);`
--   注释：建联合索引。名字规范：`idx_列名1_列名2`。
-- - `EXPLAIN SELECT ...;`
--   注释：照妖镜。加在任何 SELECT 前面，不执行查询，只返回执行计划。
--   👉 生死看淡，只看三列：
--     * `type`: 扫描类型。`ALL` (全表扫描，准备跑路) -> `index` (全索引扫描) -> `range` (范围扫描) -> `ref` (非唯一性索引查询，非常棒) -> `const` (主键/唯一索引查询，神级)。
--     * `key`: 到底用上了哪个索引。如果是 NULL，说明没用上。
--     * `Extra`: 额外信息。`Using index` (触发覆盖索引，神级)；`Using filesort` / `Using temporary` (内存排序/临时表，高并发下直接炸机)。

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：为你准备一张千万级数据的模拟空壳表。
CREATE TABLE IF NOT EXISTS high_concurrency_tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    robot_sn VARCHAR(64) NOT NULL,
    task_type VARCHAR(32) NOT NULL,
    status TINYINT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 假设表中有一个联合索引：CREATE INDEX idx_sn_status ON high_concurrency_tasks(robot_sn, status);
-- 实习生为了查某个状态的任务，写出了：
-- EXPLAIN SELECT * FROM high_concurrency_tasks WHERE status = 1;
-- ❌ 灾难：违背“最左前缀法则”。联合索引的第一列是 robot_sn，你直接查第二列 status，索引彻底失效！type 变成 ALL（全表扫描）。
-- 就算写了 EXPLAIN SELECT * FROM high_concurrency_tasks WHERE robot_sn = 'ARM-001' AND status = 1;
-- ❌ 性能瑕疵：虽然用上了索引，但因为你写了 SELECT *，你要查询 created_at 等字段，必须拿着 ID 去“回表”，Extra 里绝对不会出现 `Using index`。

-- 【实战干活：TODO】
-- 背景说明：调度中心每秒要以 10万 QPS 的并发量，轮询查询特定机器人的某些状态任务。这种级别的并发，哪怕一次回表都会让数据库瘫痪。

-- TODO 1 (挂载引擎)：请为 `high_concurrency_tasks` 表创建一个联合索引。
-- 需求：业务 99% 的高频查询是根据 `robot_sn` 和 `task_type` 这两个条件，来查出对应的任务 `status`。
-- 思考：怎么建联合索引，才能把这三个字段全包进去？
CREATE INDEX idx_sn_type_status ON high_concurrency_tasks (robot_sn, task_type, status);

DESC high_concurrency_tasks;

SELECT * FROM high_concurrency_tasks;
-- TODO 2 (覆盖查询)：写出一条高频轮询的 SELECT 语句，要求：
-- 1. 根据 `robot_sn` 和 `task_type` 进行等值过滤（随便写两个假条件即可）。
-- 2. 只查询出这台机器的 `status`（以及主键 `id`）。
-- 3. 在前面加上 EXPLAIN！
EXPLAIN
SELECT id, status
FROM high_concurrency_tasks
WHERE
    robot_sn = 'ARM-001'
    AND task_type = 'CLEAN';
-- TODO 3 (踩坑演示)：故意写出一条会破坏“最左前缀法则”、导致你刚才建的联合索引失效的 EXPLAIN 语句。
EXPLAIN SELECT id FROM high_concurrency_tasks WHERE task_type = 1;
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 执行你的 TODO 2。
-- 验收标准：观察 EXPLAIN 的输出结果。
-- 1. `type` 必须是 `ref`！
-- 2. `key` 必须是你刚才建的索引名字！
-- 3. `Extra` 必须包含 `Using index` (这意味着你成功触发了覆盖索引，干掉了回表，性能达到了巅峰)！

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 还是上面的表，你建了完美的联合索引 `idx_sn_type (robot_sn, task_type)`。
-- 后来业务加了个需求，你要查某个机器人前缀，并且指定 task_type 的数据。你写了：
-- `SELECT status FROM high_concurrency_tasks WHERE robot_sn LIKE 'ARM-10%' AND task_type = 'CLEAN';`
-- 结果线上又炸了，DBA 说你的 `task_type` 没走索引！

-- 👉 救火任务：
-- "你明明按照顺序把 robot_sn 放在前面，task_type 放在后面了，完全符合最左前缀法则！为什么 `LIKE 'ARM-10%'` 会导致后面的 `task_type` 索引失效？
-- 结合 B+ 树的底层物理排序结构，想象一下：当 `robot_sn` 处于一个范围（Range）时，它内部的 `task_type` 还是有序的吗？"
/*
因为使用了like这个模糊匹配吗？
是无序的。
*/