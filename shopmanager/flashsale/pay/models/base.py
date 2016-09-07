# -*- coding: utf-8 -*-
from core.models import BaseModel


class PayBaseModel(BaseModel):
    """ 对商城的MODEL抽象 """

    class Meta:
        abstract = True
