# encoding=utf8
from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import (
    authentication,
    permissions,
    exceptions,
)

from common.wdt import WangDianTong


class WangDianTongViewSet(viewsets.ViewSet):
    """
    GET /rest/v2/wdt/logistics
    """

    def logistics(self, request, *args, **kwargs):
        wdt = WangDianTong()
        resp = wdt.receive_logistics(request)
        return Response(resp)
