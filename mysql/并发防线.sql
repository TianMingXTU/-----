/* ================= 0. 干活指南与 API 映射 (快思考) ================= */
-- 【合并节点 3.1 ~ 3.2】：并发防线 - 事务生死局与隔离级别

-- 🧠 实用直觉：
-- 1. 事务 (Transaction)：【All or Nothing】。老板让你把 A 账户的 100 块转给 B 账户。这涉及两步 UPDATE。如果在第一步（A 扣钱）和第二步（B 加钱）之间，机房停电了，怎么办？事务就是保证这两步要么【全部成功】，要么【全部撤销（回滚）】的结界。
-- 2. ACID 特性：工业界不要背八股文，你只需要记住业务映射：
--    - A (原子性): 同生共死（靠 Undo Log 回滚日志实现）。
--    - C (一致性): 能量守恒，转账前后总金额不变。
--    - I (隔离性): 并发互不干扰。别人还没转完的账，我能不能看见？（靠锁 + MVCC 实现）。
--    - D (持久性): 只要提示转账成功，拔电源钱也不会丢（靠 Redo Log 重做日志实现）。
-- 3. 隔离级别 (Isolation Level)：控制你能看到多“脏”的数据。
--    - 读未提交 (RU)：能看到别人没提交的数据（脏读）。【工业界绝对禁用】。
--    - 读已提交 (RC)：只能看到别人提交后的数据。每次读都获取最新版本。【互联网大厂高并发系统首选】。
--    - 可重复读 (RR)：MySQL 默认级别。你开启事务那一刻，世界就被“定格”了，别人怎么改，你在这个事务里查出来的值都不变（幻读/不可重复读的折中）。【金融对账场景常用】。
--    - 串行化 (Serializable)：所有人排队办事。【性能极差，禁用】。

-- 🛠️ 核心 API (语法) 兵器谱：
-- - `START TRANSACTION;` / `BEGIN;`
--   注释：开启结界。接下来的所有增删改操作，都在内存里酝酿，别人看不见。
-- - `COMMIT;`
--   注释：落锤成交。将结界里的所有操作永久写入磁盘，世界线变动。
-- - `ROLLBACK;`
--   注释：时光倒流。发现不对劲，直接丢弃结界里的所有操作，恢复到 BEGIN 之前的状态。
-- - `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;`
--   注释：将会话级别的隔离级别降级为 RC（大厂基操）。

/* ================= 1. 环境与依赖准备 ================= */
USE ai_robotics_db;

-- ⚠️ 战争迷雾解除：为你准备一张极度危险的“机器人云平台钱包表”。
CREATE TABLE IF NOT EXISTS robot_wallets (
    account_id VARCHAR(32) PRIMARY KEY COMMENT '账户ID',
    balance DECIMAL(10, 2) NOT NULL COMMENT '账户余额'
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '机器人云平台账户钱包';

TRUNCATE TABLE robot_wallets;
-- 充值初始化：A 账户（你的总控节点）和 B 账户（外部 API 服务商）
INSERT INTO
    robot_wallets (account_id, balance)
VALUES ('ACCOUNT_A', 1000.00),
    ('ACCOUNT_B', 0.00);

SELECT * FROM robot_wallets;
/* ================= 2. 搬砖实战场 (Pragmatic Battleground) ================= */

-- 【案发现场：干活时的低级错误】
-- 实习生写的一个接口：总控节点调用了一次外部 API，需要从 A 账户扣 10 块钱，给 B 账户加 10 块钱。
-- 他直接在 Python 里连发了两条 SQL：
-- UPDATE robot_wallets SET balance = balance - 10 WHERE account_id = 'ACCOUNT_A';
-- (此时如果网络闪断、Python 进程 OOM 崩溃，下一条没发出去)
-- UPDATE robot_wallets SET balance = balance + 10 WHERE account_id = 'ACCOUNT_B';
-- ❌ 灾难：A 的钱扣了，B 没收到。公司出现了 10 块钱的财务黑洞。如果并发量是 1万/秒，公司一天就会面临法律诉讼。

-- 【实战干活：TODO】
-- 背景说明：为了修复实习生的 Bug，你需要用原生的 SQL 事务来包裹这个转账过程。

-- 实战要求：
-- 1. 显式开启事务。
-- 2. 将 A 账户扣除 500 元。
-- 3. 将 B 账户增加 500 元。
-- 4. 假设突然收到了风控系统的拦截报警，必须立即撤销上述操作。请执行回滚。

-- TODO 1: 按照要求，写出完整的事务生命周期 SQL (包含开启、两步扣款、以及最终的回滚)
-- 你的 SQL 脚本写在这里...
START TRANSACTION;

UPDATE robot_wallets
SET
    balance = balance - 10
WHERE
    account_id = "ACCOUNT_A";

UPDATE robot_wallets
SET
    balance = balance + 10
WHERE
    account_id = "ACCOUNT_B";

# COMMIT;
ROLLBACK;
/* ================= 3. 黑盒测试 (Test Cases：交差验收) ================= */

-- 运行你的 TODO 1 后，执行以下查询：
SELECT * FROM robot_wallets;

-- 打印："✅ 验收标准：A 账户的钱必须依然是 1000.00，B 账户必须依然是 0.00。能量完全守恒，回滚成功。准备下班。"

/* ================= 4. 慢思考 (事后诸葛亮：线上事故复盘) ================= */

-- 🧠 慢思考拷问 (干完活后的“惊悚”复盘)：
-- 【真实事故场景模拟】：
-- 假设你们现在的系统依然使用的是 MySQL 默认的隔离级别：可重复读 (RR)。
--
-- 场景（时空折叠）：
-- 1. [线程甲] 开启了事务（BEGIN），查询 A 账户余额，发现有 1000 元。此时它正在做复杂的业务计算，还没提交。
-- 2. [线程乙] 突然杀入，也开启了事务，直接执行 UPDATE 把 A 账户的 1000 元扣完了，并且执行了 COMMIT。
-- 3. [线程甲] 计算完毕，打算在这个事务内再次确认 A 账户余额。
--
-- 👉 救火任务：
-- "不用背概念，带入到场景里告诉我：
-- 1. 在 RR 隔离级别下，[线程甲] 第二次查到的 A 账户余额是多少？（提示：既然叫‘可重复读’，说明它产生了幻觉）
-- 1000
-- 2. 如果 [线程甲] 看到余额依然充足，决定直接执行 `UPDATE robot_wallets SET balance = balance - 100 WHERE account_id = 'ACCOUNT_A'`，底层的真实余额会被扣成负数吗？
-- 不会
-- 3. [进阶架构题]：MySQL 底层到底是通过什么核心机制（四个英文字母），让 [线程甲] 能够无锁地读取到这个‘历史快照’的？"
-- ACID