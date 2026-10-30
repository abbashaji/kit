from collections import OrderedDict


class LRU:
    def __init__(self, capacity):
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._d = OrderedDict()

    def get(self, k):
        if k not in self._d:
            return None
        self._d.move_to_end(k)
        return self._d[k]

    def put(self, k, v):
        if k in self._d:
            self._d.move_to_end(k)
        self._d[k] = v
        while len(self._d) > self.capacity:
            self._d.popitem(last=False)
