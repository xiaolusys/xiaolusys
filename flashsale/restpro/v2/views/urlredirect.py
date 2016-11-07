# encoding=utf8
import logging
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from rest_framework import viewsets

from flashsale.pay.models.user import Customer


logger = logging.getLogger('service')


class URLRedirectViewSet(viewsets.ViewSet):

    def redirect(self, request, *args, **kwargs):
        params = request.GET
        url = params.get('url') or ''
        customer_id = ''
        mama_id = ''

        customer = Customer.getCustomerByUser(user=request.user)
        if customer:
            customer_id = customer.id
            mama = customer.get_xiaolumm()
            if mama:
                mama_id = mama.id

        log = {
            'action': 'common.urlredirect',
            'customer_id': str(customer_id),
            'mama_id': str(mama_id),
        }
        log.update(params.dict())
        logger.info(log)

        val = URLValidator()
        try:
            val(url)
        except ValidationError:
            url = 'http://m.xiaolumeimei.com'

        return redirect(url)
