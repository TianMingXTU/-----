/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【业务场景/功能节点名称】：核心基建 - 约束的取舍与幂等性防御

-- 🧠 实用直觉：
-- 1. 主键 (PRIMARY KEY)：每张表的“身份证”。必须有，绝不妥协。
-- 2. 唯一约束 (UNIQUE KEY)：高并发下的“防抖/防重”神器。老板说“不能让同一个外部任务被重复执行两次”，别指望在 Python/Java 代码里做判断（并发时防不住的），直接在数据库对应字段加 UNIQUE，利用底层帮你挡住重复写入。这种设计叫做【幂等性】保障。
-- 3. 外键 (FOREIGN KEY)：【工业界红线：禁止使用物理外键！】
--    - 为什么不用？每次 INSERT/UPDATE，数据库都要去查另一张表校验，拖慢性能；高并发下极易引发死锁；后续分库分表时，物理外键直接变成灾难。
--    - 怎么替代？使用【逻辑外键】。表里依然留着 `task_id` 这个字段，但不要写 `FOREIGN KEY` 语法。数据的一致性交由你的 Python/Rust 业务代码（或分布式事务）来保证。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `PRIMARY KEY (id)`
-- - `UNIQUE KEY uk_external_job (external_job_id)`
--   注释：uk_ 是规范前缀。加了它，重复插入相同 external_job_id 时会直接报 Duplicate entry 错误，业务层捕获这个异常即可。
-- - `INDEX idx_task_id (task_id)`
--   注释：即使废弃了物理外键，关联字段依然需要加普通索引，否则后续 JOIN 或者按 task_id 查询时会全表扫描。

/* ================= 1. 环境与依赖准备 ================= */
-- 我们继续在你的机器人生态库里干活。
USE ai_robotics_db;

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 刚毕业的本科生在设计分布式任务调度系统时，写出了如下“教科书般”完美、但会被工业界直接枪毙的关联表：
CREATE TABLE rookie_nexus_tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_name VARCHAR(64) NOT NULL
);

CREATE TABLE rookie_task_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT UNSIGNED NOT NULL,
    log_info VARCHAR(255),
    -- ❌ 灾难：使用了物理外键，甚至还加了级联删除！
    CONSTRAINT fk_task FOREIGN KEY (task_id) REFERENCES rookie_nexus_tasks (id) ON DELETE CASCADE
);

-- 【实战干活：TODO】
-- 背景说明：你的分布式任务调度系统 (Nexus) 需要重构底层的状态存储。有两个核心实体：【任务表 (nexus_tasks)】和【任务执行日志表 (task_logs)】。
-- 实战要求：
-- 1. 创建 `nexus_tasks` 表：
--    - 包含主键 `id`。
--    - 包含 `global_trace_id` (全局追踪ID，字符串，32位)。为了防止上游系统重复下发相同的任务导致资源浪费，这个字段必须保证全局唯一！
-- 2. 创建 `task_logs` 表：
--    - 包含主键 `id`。
--    - 包含 `task_id`，作为关联任务表的【逻辑外键】（只存数据，不建物理约束）。
--    - 包含 `status` (状态)。
--    - 考虑到业务经常需要查询“某个任务下的所有日志”，你必须为 `task_id` 加上普通索引。
-- 3. （可选挑战）给表和字段加上清晰的 COMMENT。

-- TODO 1: 编写创建 nexus_tasks 的 SQL，重点实现防重的唯一约束...
CREATE TABLE nexus_tasks (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "主键",
    global_trace_id VARCHAR(32) UNIQUE COMMENT "全局追踪id"
);
-- TODO 2: 编写创建 task_logs 的 SQL，彻底抛弃物理外键，但要加上普通查询索引...
DROP TABLE task_logs;
CREATE TABLE task_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "主键",
    task_id BIGINT UNSIGNED COMMENT "任务id",
    status TINYINT COMMENT "状态",
    INDEX idx_task_id (task_id)
);
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 验证 1：检查物理结构，如果 task_logs 里出现了 FOREIGN KEY 关键字，说明你不合格。
SHOW CREATE TABLE task_logs;

-- 验证 2：验证防抖/防重机制（幂等性）。
-- TODO: 尝试向 nexus_tasks 连续插入两条具有相同 global_trace_id 的数据。
INSERT INTO nexus_tasks (global_trace_id) VALUES ("trace_10");
-- 预期结果：第一条成功，第二条数据库层面直接报错 (Duplicate entry)，从而保护了系统不会重复执行任务。
INSERT INTO nexus_tasks (global_trace_id) VALUES ("trace_10");
/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 假设你没有听从架构师的警告，在线上依然使用了带 `ON DELETE CASCADE` 的物理外键。
-- Nexus 调度系统跑了几个月，`rookie_task_logs` 里积攒了 5 亿条日志。
-- 某天，老板让你清理一下三个月前的历史废弃任务。你轻描淡写地在 `rookie_nexus_tasks` 表里执行了一句：
-- `DELETE FROM rookie_nexus_tasks WHERE status = 'DEPRECATED';` （假设命中了 10 万个历史任务）。
--
-- 结果回车一敲，整个调度系统全线崩溃，所有正在向 `rookie_task_logs` 写新日志的线程全部处于 `Lock Wait Timeout` 状态。
--
-- 👉 救火任务：
-- "为什么删除了区区 10 万个主表任务，会把整个系统的写入全部卡死？结合 `ON DELETE CASCADE` 和 InnoDB 的锁机制，分析一下底层到底发生了多可怕的连锁反应？"
/*
因为使用了物理外键的话，会检查外键关联的表，导致了整个系统的写入全部卡死，因为都是在检查了。
*/