-- Active: 1778071962577@@127.0.0.1@3306@heima
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