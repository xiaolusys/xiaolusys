# encoding=utf8
from datetime import date
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.response import Response
from rest_framework import (
    authentication,
    permissions,
    exceptions,
)

from flashsale.pay.models.user import Customer
from shopapp.weixin.utils import gen_mama_custom_qrcode_url


class QRcodeViewSet(viewsets.ModelViewSet):
    """
    ## GET /rest/v2/qrcode/get_wxpub_qrcode　　根据小鹿妈妈 id 创建小鹿美美公众号临时二维码
    return
    {
        'code': 0,
        'info': '',
        'qrcode_link': 'http://xxxx'
    }
    """

    queryset = Customer.objects.all()
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def list(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    @list_route()
    def get_wxpub_qrcode(self, request, *args, **kwargs):
        customer = Customer.getCustomerByUser(user=request.user)

        if not customer:
            return Response({"code": 7, "info": u"用户未找到"})

        mama = customer.get_xiaolumm()
        if mama:
            mama_id = mama.id
        else:
            return Response({"code": 1, "info": u"不是小鹿妈妈"})

        qrcode_link, _ = gen_mama_custom_qrcode_url(mama_id)

        return Response({'code': 0, 'info': u'', 'qrcode_link': qrcode_link})

    def retrieve(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def partial_update(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')

    def destroy(self, request, *args, **kwargs):
        raise exceptions.APIException('METHOD NOT ALLOWED')
