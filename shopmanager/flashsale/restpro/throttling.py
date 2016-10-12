# coding=utf-8
from rest_framework.throttling import ScopedRateThrottle


class TestScopedRateThrottle(ScopedRateThrottle):
    scope = 'test'