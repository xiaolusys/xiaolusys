# coding: utf8
from __future__ import absolute_import, unicode_literals

import hashlib
from cStringIO import StringIO
from django.contrib import admin

from core.options import log_action, ADDITION, CHANGE
from core.upload import upload_public_to_remote, generate_public_url
from ..fengchao.models import FengchaoOrderChannel

from . import sdks

import logging
logger = logging.getLogger(__name__)

@admin.register(FengchaoOrderChannel)
class FengchaoOrderChannelAdmin(admin.ModelAdmin):
    list_display = ('channel_id', 'channel_name', 'channel_type', 'channel_client_id', 'status')
    list_filter = ('channel_type', )
    search_fields = ['=channel_id', '=channel_client_id']
    ordering = ('-modified',)

    def response_change(self, request, obj, *args, **kwargs):
        if not obj.status:
            try:
                sdks.create_fengchao_order_channel(
                    obj.channel_client_id,
                    obj.channel_name,
                    obj.channel_type,
                    obj.channel_id,
                )
            except Exception, exc:
                self.message_user(request, u"更新蜂巢订单渠道失败：%s" % (exc.message))
                logger.error(u"更新蜂巢订单渠道失败：%s" % (exc.message), exc_info=True)

        return super(FengchaoOrderChannelAdmin, self).response_change(request, obj, *args, **kwargs)