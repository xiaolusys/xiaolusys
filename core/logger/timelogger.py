import time

import logging
logger = logging.getLogger(__name__)

def log_consume_time(func):
    def _warp(*args, **kwargs):
        start = time.time()
        resp = func(*args, **kwargs)
        end = time.time()
        logger.info('%s consumes: %.5f'%(func.__name__, end - start))
        return resp
    return _warp