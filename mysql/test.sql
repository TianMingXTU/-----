-- Active: 1778071962577@@127.0.0.1@3306@test_heima
CREATE DATABASE IF NOT EXISTS bigdata_db DEFAULT CHARACTER SET utf8mb4;

SHOW DATABASES;

USE bigdata_db;

SELECT DATABASE();

DROP DATABASE IF EXISTS bigdata_db;

CREATE Table stu3 (
    id INT,
    age INT,
    high FLOAT,
    name VARCHAR(100),
    birthday DATE,
    money DECIMAL(6, 2)
);

DESC stu3;

ALTER Table stu3 add tab VARCHAR(50);

ALTER Table stu3 CHANGE tab tab INT;

ALTER Table stu3 MODIFY tab TEXT;

ALTER Table stu3 DROP tab;

SELECT * FROM stu3;

INSERT into stu3 (age, money) VALUES (21, 123), (221, 1223);

INSERT INTO
    stu3
VALUES (
        1,
        2,
        3,
        "name",
        "2025/12/01",
        451
    ),
    (
        11,
        21,
        31,
        "name1",
        "2025/10/01",
        4151
    );

#创建数据库
CREATE DATABASE if NOT EXISTS test_heima;

DROP DATABASE if EXISTS test_heima;

#使用数据库
USE test_heima;

#查看数据库
show DATABASES;

SELECT DATABASE();

#创建表
CREATE Table stu1
(
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "主键",
    name VARCHAR(20) COMMENT "名字" 
);

#展示表
SHOW TABLES;

DESC stu1;

#删除表
DROP TABLE stu1;

TRUNCATE Table stu1;

DELETE FROM stu1;

# 插入数据

INSERT INTO stu1 (name) VALUES ("1"),("2");

UPDATE stu1 SET name = "小米" WHERE id = 1;

SELECT * FROM stu1;

#修改
ALTER Table stu1 ADD skill VARCHAR(10);

ALTER Table stu1 CHANGE skill skill2 INT;

CREATE Table stu2 (
    id INT,
    name VARCHAR(20),
    age TINYINT
);

DESC stu2;

ALTER TABLE stu2 ADD PRIMARY KEY (id);

ALTER Table stu2 DROP PRIMARY KEY;

ALTER Table stu2 CHANGE id id INT PRIMARY KEY;

CREATE Table ai_system_logs (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT "主键",
    module_name VARCHAR(50) COMMENT "模块名",
    run_time FLOAT NOT NULL COMMENT "耗时",
    created_at TIMESTAMP
);

