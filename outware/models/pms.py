# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import models
from core.models import BaseModel


class OutwareSupplier(BaseModel):

    outware_account = models.ForeignKey('outware.OutwareAccount', verbose_name=u'关联账号')

