-- Active: 1778071962577@@127.0.0.1@3306@db_ai_train
CREATE DATABASE IF NOT EXISTS db_ai_train;

USE db_ai_train;

CREATE TABLE ai_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_name VARCHAR(100),
    model_name VARCHAR(100),
    run_time INT,
    status VARCHAR(20),
    created_at DATETIME
);

INSERT INTO
    ai_tasks (
        task_name,
        model_name,
        run_time,
        status,
        created_at
    )
VALUES (
        '数据清洗任务-001',
        'gpt-4',
        120,
        'SUCCESS',
        '2024-01-01 10:00:00'
    ),
    (
        '数据清洗任务-002',
        'gpt-4',
        95,
        'SUCCESS',
        '2024-01-01 10:10:00'
    ),
    (
        '特征抽取任务-001',
        'bert-base',
        180,
        'FAILED',
        '2024-01-01 10:20:00'
    ),
    (
        '特征抽取任务-002',
        'bert-base',
        160,
        'SUCCESS',
        '2024-01-01 10:30:00'
    ),
    (
        '样本去重任务-001',
        'llama-7b',
        300,
        'SUCCESS',
        '2024-01-01 10:40:00'
    ),
    (
        '样本去重任务-002',
        'llama-7b',
        280,
        'RUNNING',
        '2024-01-01 10:50:00'
    ),
    (
        '异常值检测任务-001',
        'gpt-4',
        130,
        'SUCCESS',
        '2024-01-01 11:00:00'
    ),
    (
        '异常值检测任务-002',
        'bert-base',
        210,
        'SUCCESS',
        '2024-01-01 11:10:00'
    ),
    (
        '训练前统计任务-001',
        'llama-7b',
        260,
        'FAILED',
        '2024-01-01 11:20:00'
    ),
    (
        '训练前统计任务-002',
        'gpt-4',
        100,
        'SUCCESS',
        '2024-01-01 11:30:00'
    );

SELECT model_name
FROM ai_tasks
WHERE
    status = "SUCCESS"
GROUP BY
    model_name
HAVING
    AVG(run_time) > 10.5
ORDER BY AVG(run_time) DESC;

DELETE FROM ai_tasks WHERE id = 100;

