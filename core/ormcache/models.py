from django.db import models
from django.conf import settings
from . import signals
import logging

logger = logging.getLogger(__name__.split('.')[-1])

def cache_hit_logger(sender, *args, **kwargs):
    if settings.DEBUG:
        logger.debug('cache hit:%s'%sender)
    
def cache_missed_logger(sender, *args, **kwargs):
    if settings.DEBUG:
        logger.debug('cache missed:%s'%sender)
    
def cache_invalidated_logger(sender, *args, **kwargs):
    if settings.DEBUG:
        logger.debug('cache invalidated:%s'%sender)

signals.cache_hit.connect(cache_hit_logger);
signals.cache_missed.connect(cache_missed_logger);
signals.cache_invalidated.connect(cache_invalidated_logger);