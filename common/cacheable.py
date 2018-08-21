# coding: utf-8

from datetime import datetime, timedelta
from functools import wraps
import threading


class LocalCacheable(object):
    # 缓存30分钟
    interval = 60 * 30

    @staticmethod
    def reload(f):

        @wraps(f)
        def _wrapper(self, *args, **kwargs):
            now = datetime.now()
            if self.last_updated(*args, **kwargs) + timedelta(
                    seconds=self.interval) < now:
                with self.lock:
                    self.load(*args, **kwargs)
                    self.set_last_updated(now, *args, **kwargs)
            return f(self, *args, **kwargs)

        return _wrapper

    def __init__(self):
        self.lock = threading.Lock()
        self._last_updated = datetime.min

    def last_updated(self, *args, **kwargs):
        return self._last_updated

    def set_last_updated(self, now, *args, **kwargs):
        self._last_updated = now

    def load(self, *args, **kwargs):
        raise NotImplementedError()
