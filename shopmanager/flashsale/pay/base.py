# -*- coding: utf-8 -*-
from core import models

class PayBaseModel(models.CacheModel):
    """ 对商城的MODEL抽象 """
    class Meta:
        abstract = True
        
        