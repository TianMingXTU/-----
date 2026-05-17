class TaskMonior:
    total_tasks = 0

    def __init__(self):
        TaskMonior.total_tasks += 1


t1 = TaskMonior()
print(t1.total_tasks)
t2 = TaskMonior()
print(t2.total_tasks)

"""
from join where group by having select order by limit
"""

import functools
import time


def time_logger(t=None):
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            print(f"耗时:{time.time()-start_time}")
            return result

        return wrapper

    return decorate


import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind(("127.0.0.1", 8888))

server.listen(5)

while True:
    try:
        socket_ap, socket_info = server.accept()
        result = socket_ap.recv(1024).decode("utf-8")
        if result == "exit":
            break
    finally:
        socket_ap.close()

server.close()


class DataTransformer:
    def __init__(self, scale):
        self.scale = scale

    def __call__(self, n):
        return n * self.scale


transformer_obj = DataTransformer(10)
print(transformer_obj(5))
