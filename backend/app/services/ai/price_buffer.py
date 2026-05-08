from collections import deque

class PriceBuffer:
    def __init__(self, maxlen: int = 20):
        self.buffer = deque(maxlen=maxlen)

    def add(self, price: float):
        self.buffer.append(price)

    def get(self):
        return list(self.buffer)