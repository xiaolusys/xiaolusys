from django.db import models

from .mixins import CachedManagerMixin

class CacheManager(CachedManagerMixin, models.Manager):
    
    def get_queryset(self):
        """
        Overrides Django builtin
        """
        super_ = super(CacheManager, self)
        if hasattr(super_, "get_queryset"):
            # Django > 1.6
            return super_.get_queryset()
        # Django <= 1.5
        return super_.get_query_set()

    # Support for Django <= 1.5
    get_query_set = get_queryset