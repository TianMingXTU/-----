-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【业务场景/功能节点名称】：核心搬砖 - 数据的增、删、改 (DML) 与删库防线

-- 🧠 实用直觉：
-- 1. 批量插入 (Batch Insert)：老板让你导 1 万条数据，你要是敢在 Python 代码里写个 `for` 循环连 1 万次数据库执行 INSERT，你的网络 IO 和数据库连接池会当场爆炸。工业标准做法：把多条数据拼成一条 SQL 批量发过去。
-- 2. 夺命 UPDATE / DELETE：【工业界绝对红线】永远、永远、永远不要写出不带 WHERE 条件的更新或删除语句！一旦手抖回车，全表数据瞬间灰飞烟灭。
-- 3. 软删除 (Soft Delete)：在真实的商业系统中，数据就是资产。绝大多数核心表（如订单、用户、任务记录）绝对不允许执行物理 DELETE。所谓的“删除”，其实是将一个状态字段（比如 is_deleted 或 status） UPDATE 为特定值。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `INSERT INTO table_name (col1, col2) VALUES (v1, v2), (v3, v4), ...;`
--   注释：批量插入的终极写法。一次网络开销，搞定多条数据。
-- - `UPDATE table_name SET col1 = v_new WHERE 唯一索引列 = ?;`
--   注释：更新操作。防坑指南：WHERE 后面尽量跟主键或唯一索引，确保精准打击。在执行 UPDATE 之前，先写个 SELECT 确认一下受影响的范围！
-- - `DELETE FROM table_name WHERE id = ?;`
--   注释：物理删除。非核心业务日志表可以偶尔用用，核心表禁用。

/* ================= 1. 环境与依赖准备 ================= */
-- 我们回到你的老地盘
USE ai_robotics_db;

SELECT DATABASE();
-- 强烈建议：检查你的数据库是否开启了“安全更新模式” (防止没带 WHERE 的误杀)
SHOW VARIABLES LIKE 'sql_safe_updates';
-- 如果是 OFF，说明你在裸奔。工业界很多测试环境会强行 SET sql_safe_updates = 1;
SET sql_safe_updates = 1;
/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 某外包员工接到需求：“把状态为‘故障’的机器人的固件版本都改成 v2.0”。
-- 他本来想这么写：UPDATE robots SET firmware_version = 'v2.0' WHERE status = 99;
-- 结果键盘一滑，选中了前半截直接按了执行：
-- ❌ 灾难：UPDATE robots SET firmware_version = 'v2.0';
-- 结果：全公司所有机器人的固件版本号都被强行覆盖成了 v2.0，且无法撤销。

-- 【实战干活：TODO】
-- 背景说明：我们继续用你之前（在节点 0.1 中）建好的 `robots` 表。现在新到了一批机械臂，需要入库并初始化状态。
-- 你的表结构回顾：`robots` (id, robot_sn, status, firmware_version)
-- 状态字典约定：0-离线，1-在线，-1-已报废(软删除)

-- 实战要求：
-- 1. 使用【一条 SQL 语句】将 3 台新的机器人批量插入到表中。SN 号分别为 'ARM-001', 'ARM-002', 'ARM-003'，状态默认为 0，版本为空。
-- 2. 业务变动：由于 'ARM-002' 出厂质检不合格，需要立刻进行【软删除】。请写出对应的 SQL，通过更新 status 字段来将其标记为报废（-1）。
-- 3. 业务变动：给 'ARM-001' 更新固件版本为 'v3.1.5'，同时将其状态上线（改为 1）。请写出同时更新多个字段的 SQL。

DROP TABLE robots;

-- TODO 1: 编写批量 INSERT 语句...
insert INTO
    robots (
        robot_sn,
        status,
        firmware_version
    )
VALUES ("ARM-001", 0, NULL),
    ("ARM-002", 0, NULL),
    ("ARM-003", 0, NULL);

SELECT * FROM robots;

-- TODO 2: 编写基于 robot_sn 的软删除 (UPDATE) 语句...
update robots SET status = -1 WHERE robot_sn = 'ARM-002';
-- TODO 3: 编写同时更新多个字段的 UPDATE 语句...
UPDATE robots
SET
    status = 1,
    firmware_version = 'v3.1.5'
WHERE
    robot_sn = 'ARM-001';
;
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 查询当前表里的存活机器状态
SELECT
    id,
    robot_sn,
    status,
    firmware_version
FROM robots
WHERE
    status != -1;

-- 打印："✅ 如果查出来的结果只有 ARM-001 (版本v3.1.5, 状态1) 和 ARM-003 (状态0)，并且没有 ARM-002，说明你的软删除和更新都对了。准备下班。"

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 假设你的机器没有开启 `sql_safe_updates`。
-- 某天凌晨 2 点你在进行生产环境数据订正时，严重的手误出现了。你原本想执行 `DELETE FROM task_logs WHERE created_at < '2025-01-01';`，结果漏圈了 WHERE 条件。
-- 一瞬间，核心日志表 `task_logs` 里的上亿条数据被全部清空！

-- 👉 救火任务：
-- "冷汗下来了吧？现在代码已经执行完了，数据全没了。作为公司的骨干工程师，你不能坐着等死。在 MySQL 的 InnoDB 引擎下，如果发生了这种不带 WHERE 的灾难级 UPDATE/DELETE，我们唯一的一根救命稻草是什么？DBA 会用什么核心技术手段（提示：与日志有关）把数据给你捞回来？"
/*
我们得使用sql_safe_updates或者是sql_safe_delete啊。DBA在日志里面捞以前执行过的命令，重新进执行插入命令，能够就会部分数据。
*/