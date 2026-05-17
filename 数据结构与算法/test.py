from typing import List

num = [0, 1, 0, 3, 12]
num = [1, 0, 3]


def move_zore(num: List[int]):
    slow = 0
    for fast in range(len(num)):
        if num[fast] != 0:
            num[slow], num[fast] = num[fast], num[slow]
            slow += 1
    return num


print(move_zore(num))


"""
0 1 0 3 12
s 1 3 12 0 0
f 0 1 0 3 12

"""
