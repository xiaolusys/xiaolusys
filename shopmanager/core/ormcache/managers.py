from django.db import models

from .mixins import CachedManagerMixin

class CacheManager(CachedManagerMixin, models.Manager):
    pass