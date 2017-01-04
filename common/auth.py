# encoding=utf8
from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions
from django.core.cache import cache

from flashsale.pay.models.user import Customer


class WeAppAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.GET.get('x-token') or request.POST.get('x-token')
        if not token:
            return None

        try:
            session = cache.get(token)
            openid = session['openid']
            unionid = session['unionid']

            customer = Customer.objects.get(unionid=unionid)
            user = customer.user
        except Exception:
            raise exceptions.AuthenticationFailed('No such user')

        return (user, None)