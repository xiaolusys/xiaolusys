import types
from oneapm_ci_sdk.onestatsd.base import OneStatsd


def incr(self, metric, value=1, tags=None, sample_rate=1):
    return self.increment(metric, value, tags, sample_rate)

def timing(self, stat, delta, rate=1):
    return self.gauge(stat, delta)

def StatsClient(host, port, prefix):
    client = OneStatsd(host=host, port=port)
    client.incr = types.MethodType(incr, client)
    client.timing = types.MethodType(timing, client)
    return client
