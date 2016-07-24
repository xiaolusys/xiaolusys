# coding=utf-8
from supplychain.supplier.models import BuyerGroup
from django.http import HttpResponse
from django.views.generic import View
from core.options import log_action, CHANGE, ADDITION


class BuyerGroupSave(View):
    def post(self, request):
        content = request.REQUEST
        name = content.get('name')
        group = content.get('group')

        buyer_groups = BuyerGroup.objects.filter(buyer_name=name)
        if buyer_groups.count() > 0:  # if the name is same then change all
            for buyer in buyer_groups:
                buyer.buyer_name = name
                buyer.buyer_group = group
                buyer.save()
                log_action(request.user.id, buyer, CHANGE, u'修改到{0}'.format(group))
                return HttpResponse('changeok')
        else:
            buyer = BuyerGroup()
            buyer.buyer_group = group
            buyer.buyer_name = name
            buyer.save()
            log_action(request.user.id, buyer, ADDITION, u'创建用户')
            return HttpResponse('createok')


