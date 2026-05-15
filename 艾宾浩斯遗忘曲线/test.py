class BaseTask:
    def __init__(self, task_id):
        self.task_id = task_id

    def execute(self):
        pass


class NetworkTask(BaseTask):
    def __init__(self, task_id, ip_addr):
        self.ip_addr = ip_addr
        super().__init__(task_id)

    def execute(self):
        print(f"task_id:{self.task_id}")
        print(f"ip_addr:{self.ip_addr}")
