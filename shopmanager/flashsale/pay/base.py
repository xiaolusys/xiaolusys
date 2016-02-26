# -*- coding: utf-8 -*-
from core.models import BaseModel,CacheModel

class PayBaseModel(CacheModel):
    """ 对商城的MODEL抽象 """
    class Meta:
        abstract = True
        
        