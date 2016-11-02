# coding: utf-8
# cachelock.py
# 内存锁 - 进程间互斥锁
import time
import json
import hashlib
from django.core.cache import cache


class CacheLockedException(BaseException):
    """ 内存锁占用异常 """
    pass


class CacheLock:
    """内存锁
    """

    def __init__(self, cache_key, cache_time, lock_wait=True):
        self.cache_key = cache_key
        self.cache_time = cache_time
        self.lock_wait = lock_wait

    def gen_cache_value(self):
        return time.time()

    def acquire(self):
        # 内存上锁
        cache_value = cache.get(self.cache_key, None)
        if cache_value and cache_value > 0:
            raise CacheLockedException(u'key:%s had been locked' % self.cache_key)
            # TODO:锁等待处理机制实现
        cache_value = self.gen_cache_value()
        cache.set(self.cache_key, cache_value, self.cache_time)

    def release(self):
        # 内存解锁
        try:
            cache.set(self.cache_key, 0, 0)
        except:
            pass


def get_func_cache_key(*args, **kwargs):
    return hashlib.sha256(u'.'.join([
        json.dumps(sorted([str(s) for s in args])).encode('utf-8'),
        json.dumps(sorted(['%s=%s' % (k, v) for k, v in kwargs])).encode('utf-8')
    ])).hexdigest()


def cache_lock(cache_time=0, lock_wait=False):
    """ cache_time:内存锁时间，lock_wait:锁是否等待 """

    def func_wraper(func):
        def wraper(*args, **kwargs):
            cache_key = get_func_cache_key(func.__name__, *args, **kwargs)
            lock = CacheLock(cache_key, cache_time, lock_wait=lock_wait)
            try:
                lock.acquire()
                resp = func(*args, **kwargs)
                lock.release()
                return resp
            except CacheLockedException:
                pass
            except:
                lock.release()

        return wraper

    return func_wraper


@cache_lock(cache_time=10)
def test_lock(a, b=None):
    time.sleep(10)
    return a + b


class TestLock():
    @cache_lock(cache_time=10 * 60)
    def lock(self, a, b=None):
        return a + b
