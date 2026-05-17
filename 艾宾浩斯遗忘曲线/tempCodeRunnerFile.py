class DataTransformer:
    def __init__(self, scale):
        self.scale = scale

    def __call__(self, n):
        return n * self.scale


transformer_obj = DataTransformer(10)
print(transformer_obj(5))