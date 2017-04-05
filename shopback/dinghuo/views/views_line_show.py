# coding=utf-8
import datetime
import json

from django.http import HttpResponse
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework import permissions
from rest_framework.response import Response

from ..models import SaleInventoryStat


class InventoryDataLineShow(APIView):
    """　库存数量数据　"""
    template_name = "inventory/inventory.html"
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer, TemplateHTMLRenderer)
    queryset = SaleInventoryStat.objects.all()

    def get(self, request):
        content = request.GET
        df = content.get("df", datetime.date.today() - datetime.timedelta(days=30))
        dt = content.get("dt", datetime.date.today())
        if isinstance(dt, str):
            df = datetime.datetime.strptime(df, '%Y-%m-%d')
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, '%Y-%m-%d')
        data_url = '/sale/dinghuo/stats/'
        title = '入库出库库存'
        return Response({"dt": dt, "df": df, "data_url": data_url, 'title': title})

    def post(self, request):
        content = request.POST
        df = content.get("df", datetime.date.today() - datetime.timedelta(days=30))
        dt = content.get("dt", datetime.date.today())
        if isinstance(dt, str):
            df = datetime.datetime.strptime(df, '%Y-%m-%d')
        if isinstance(dt, str):
            dt = datetime.datetime.strptime(dt, '%Y-%m-%d')
        stats = self.queryset.filter(stat_date__gte=df, stat_date__lte=dt)
        data = []
        for stat in stats:
            x = model_to_dict(stat,
                              fields=["newly_increased", "not_arrive", "arrived", "deliver",
                                      "inventory", "stat_date", "category"])
            data.append(x)
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder),
                            content_type="application/json")
