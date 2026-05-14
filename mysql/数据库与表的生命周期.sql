-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【业务场景/功能节点名称】：系统基建 - 数据库与数据表的生命周期管理 (DDL)

-- 🧠 实用直觉：
-- 把 MySQL 想象成一片空地（Server）。
-- CREATE DATABASE：圈一块地（数据库），指定好这块地的“语言环境”（字符集），防止以后乱码。
-- CREATE TABLE：在地上盖仓库（表）。必须定好柱子（列），并且一定要有一个主心骨（主键 Primary Key）。
-- ALTER TABLE：房子盖好后，老板突然要求加个窗户/拆个门（修改表结构）。
-- DROP TABLE：强拆。干活时极其危险，必须看清环境！

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `CREATE DATABASE IF NOT EXISTS db_name DEFAULT CHARACTER SET utf8mb4;`
--   注释：建库的标准起手式。防重复报错，且直接锁死 utf8mb4（别用 utf8，存不了 Emoji！）。
-- - `USE db_name;`
--   注释：切库。干活前必须明确自己到底在哪块地上盖房子。
-- - `CREATE TABLE table_name ( column_name TYPE Constraints, ... );`
--   注释：建表。
-- - `ALTER TABLE table_name ADD COLUMN col_name TYPE;`
--   注释：在线加字段。
-- - `DROP TABLE IF EXISTS table_name;`
--   注释：删表防错写法。

/* ================= 1. 环境与依赖准备 ================= */
-- 打开你的终端或 SQL 客户端，连接到本地或测试环境的 MySQL
-- 登入命令参考：mysql -u root -p
SELECT VERSION();
-- 确认一下你在用什么版本的兵器 (MySQL 5.7 还是 8.0?)

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 新手建表，又糙又危险：没有主键，没有字符集，没有注释（接盘侠看着直骂娘）。
CREATE TABLE rookie_user (
    id INT, -- ❌ 错漏百出：没主键，没自增，没 Unsigned
    name VARCHAR(50), -- ❌ 没注释，不知道是用户名还是真实姓名
    created_at DATETIME -- ❌ 没默认值，每次都要在代码里手动传时间
);

-- 【实战干活：TODO】
-- 背景说明：公司马上要上线一个新的 AI 机器人管理平台，老板让你负责底层的数据基建。
-- 需求：建一个用来存储“机器人设备状态”的库和表。
-- 实战要求：
-- 1. 创建数据库 `ai_robotics_db`，必须支持所有的表情符号和特殊字符（提示：utf8mb4）。
-- 2. 切换到该数据库。
-- 3. 创建一张名为 `robots` 的表。要求：
--    - `id`: 无符号整数，主键，自动递增。
--    - `robot_sn`: 机器人序列号，字符串，最长 64，不能为空。
--    - `status`: 状态，微小整数 (TINYINT)，默认值给 0（代表离线）。
--    - 每列都必须加上 COMMENT 注释！
-- 4. 业务变更：老板突然要求在表里加一列 `firmware_version` (固件版本，字符串类型，最长 32)。

-- TODO 1: 写出建库和切库的 SQL...
CREATE DATABASE IF NOT EXISTS ai_robotics_db DEFAULT CHARACTER SET utf8mb4;

USE ai_robotics_db;
-- TODO 2: 写出创建 robots 表的规范 SQL...
DROP TABLE IF EXISTS robots;
CREATE TABLE robots (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "id",
    robot_sn VARCHAR(64) NOT NULL COMMENT "机器人序列号",
    status TINYINT DEFAULT 0 COMMENT "状态"
);
-- TODO 3: 写出追加 firmware_version 字段的 ALTER 语句...
ALTER TABLE robots ADD COLUMN firmware_version VARCHAR(16);
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */
DESC robots;
-- 怎么向 QA 或架构师证明你的活儿干对了？执行以下语句：
SHOW DATABASES LIKE 'ai_robotics_db';

SHOW TABLES;
-- 核心验收：查看建表的真正物理结构和字符集
SHOW CREATE TABLE robots;
-- 打印："✅ 如果显示含有 PRIMARY KEY, AUTO_INCREMENT 且 DEFAULT CHARSET=utf8mb4，准备下班。"

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 平台平稳运行了半年，`robots` 表里积累了 2000 万条设备的活跃记录。
-- 某天下午 3 点（业务高峰期），为了配合前端展示，你直接在生产环境执行了你刚才写的 `ALTER TABLE robots ADD COLUMN last_login_ip VARCHAR(64);`。
-- 结果敲下回车的一瞬间，全公司的机器人设备全部掉线，后台数据库 CPU 瞬间打满，所有的 SELECT 和 UPDATE 全部被阻塞！系统直接瘫痪！

-- 👉 救火任务："别慌，抬起头来看看底层。在传统的 MySQL 5.7 环境下，对一张 2000 万级别的大表直接执行 ALTER TABLE 加字段，底层到底发生了什么？为什么会把全表锁死？在工业界，DBA 都是怎么给这种超大表加字段的？"
/*
我认为吧ALTER是会将所有的数据放到内存里面，才能加字段，这样就导致了CPU和内存爆满。采用离线加字段吗？
*/