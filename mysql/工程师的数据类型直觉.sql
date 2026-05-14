-- Active: 1778071962577@@127.0.0.1@3306@ai_robotics_db
/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【业务场景/功能节点名称】：核心基建 - 工业级数据类型的抉择

-- 🧠 实用直觉：
-- 建表选类型就像在流水线上选包装盒。盒子太小（比如用 INT 存手机号），装不下直接溢出崩溃；盒子太大（万物皆 VARCHAR(255)），极度浪费内存且拖慢查询。
-- 记住以下工业界“无脑”映射法则：
-- 1. 业务主键 / 雪花算法 ID -> 无脑选 `BIGINT UNSIGNED`。千万别用 INT，业务一爆表，主键插不进去，全站宕机。
-- 2. 钱 / 交易金额 -> 无脑选 `DECIMAL(M, D)`。敢用 FLOAT / DOUBLE 存钱，精度丢失导致对不上账，明天财务就会提刀来找你。
-- 3. 状态码 / 枚举 / 布尔值 -> `TINYINT` (配合 UNSIGNED)。占 1 个字节，又快又省。
-- 4. 变长字符串 -> `VARCHAR(N)`。N 代表的是“字符数”而不是字节数，按需给长度，不要偷懒全写 255。
-- 5. 记录时间 -> 现代架构中，国内业务推荐 `DATETIME`（范围大，无时区烦恼）。`TIMESTAMP` 虽然能自动转时区，但有著名的“2038 年虫”问题（超过 2038 年就溢出）。
-- 🛠️ 核心 API (语法) 兵器谱：
-- - `BIGINT UNSIGNED`
--   注释：8字节，无符号。能存到 1844 亿亿，够你的业务活到宇宙毁灭。
-- - `DECIMAL(10, 2)`
--   注释：精准计算的高级货。10代表总位数，2代表小数位（即最大支持千万级别，精确到分）。
-- - `VARCHAR(N)`
--   注释：变长字符串，用多少占多少，但 N 必须明确。
-- - `DATETIME DEFAULT CURRENT_TIMESTAMP`
--   注释：建表神器，插入时自动填充当前时间，连业务代码里的 `new Date()` 都省了。

/* ================= 1. 环境与依赖准备 ================= */
-- 确保你依然停留在刚才创建的 `ai_robotics_db` 数据库中。
USE ai_robotics_db;

/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 实习生设计的电商订单表，充斥着随时爆炸的定时炸弹：
CREATE TABLE rookie_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY, -- ❌ 灾难 1：订单量一上来，INT 瞬间上限（21亿），系统停止接单。
    total_price DOUBLE, -- ❌ 灾难 2：浮点数存钱，0.1 + 0.2 = 0.30000000000000004，等着赔钱吧。
    user_phone INT, -- ❌ 灾难 3：用 INT 存手机号（11位），13开头就超过了 INT 最大值直接报错。
    remark VARCHAR(255) -- ❌ 灾难 4：无脑 255，建临时表排序时会消耗大量无谓内存。
);

-- 【实战干活：TODO】
-- 背景说明：之前的机器人平台需要接入计费系统。老板让你建一张名为 `robot_billing_orders`（机器人计费订单） 的表。
-- 实战要求：
-- 1. `id`: 物理主键，必须顶得住海量数据增长。
-- 2. `order_no`: 业务订单号（通常是 32 位字符串），必须唯一且不能为 NULL。
-- 3. `amount`: 订单扣费金额，必须能精确到小数点后两位，最高支持百万级扣费即可。
-- 4. `billing_status`: 计费状态（0-未扣费，1-已扣费，2-扣费失败），使用最省空间的整数类型。
-- 5. `created_at`: 创建时间，要求在插入数据时，数据库能自动填入当前时间。
-- 6. 所有字段必须有 COMMENT 注释。

-- TODO 1: 擦掉实习生的代码，写出符合上述工业级要求的 CREATE TABLE 语句...
DROP TABLE robot_billing_orders;

CREATE TABLE robot_billing_orders (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "主键",
    order_no VARCHAR(32) UNIQUE NOT NULL COMMENT "业务订单号",
    amount DECIMAL(9, 2) COMMENT "订单扣费金额",
    billing_status TINYINT COMMENT "计费状态",
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT "创建时间"
);
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 插入一条极限边缘测试数据，看看你的表能不能扛得住。
-- TODO: 自己写一条 INSERT 语句，插入一个包含最大允许金额、且不主动传 created_at 的数据。
insert INTO
    robot_billing_orders (
        order_no,
        amount,
        billing_status
    )
VALUES ("机器人业务线1", 254.212, 1);

-- 验证：SELECT * FROM robot_billing_orders; 看看金额是否精准，时间是否自动生成了！
SELECT * FROM robot_billing_orders;
/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 你接手了一个老旧的 ERP 系统，里面有一张核心表 `tb_users`，主键用的是 `id INT AUTO_INCREMENT`。
-- 某天半夜 2 点，系统忽然报警，所有新用户注册全部失败，报错 `Duplicate entry '2147483647' for key 'PRIMARY'`。
--
-- 👉 救火任务：
-- "这就是典型的 INT 溢出惨案！现在的首要任务是恢复系统。如果不改变业务代码，只在数据库层面操作，你能直接把 `id INT` 改成 `id BIGINT` 吗？如果这张表有 5000 万行数据，直接用 ALTER TABLE 强改类型，会导致什么灾难后果？你的紧急预案是什么？"
/*
应该是不能改变的类型的吧，我们做的事情只能进行数据迁移。直接用 ALTER TABLE 强改类型，导致CPU和其他的查询业务卡死。因为ALTER无法在大数据里面使用。
*/