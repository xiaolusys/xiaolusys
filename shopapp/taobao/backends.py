import time
import json
import urllib
import urllib2
import urlparse
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.backends import RemoteUserBackend
from django.conf import settings
from .apis import *


"""
token {
    "w2_expires_in": 0,
    "taobao_user_id": "121741189",
    "taobao_user_nick": "%E4%BC%98%E5%B0%BC%E5%B0%8F%E5%B0%8F%E4%B8%96%E7%95%8C",
    "w1_expires_in": 1800,
    "re_expires_in": 2592000,
    "r2_expires_in": 0,
    "hra_expires_in": "1800",
    "expires_in": 86400,
    "token_type": "Bearer",
    "refresh_token": "6201a02d59ZZ5a04911942af136db8a901de3efa62ff63c121741189",
    "access_token": "6202b025cfhj953ffb3b2bdba4aedac383f01cf6ed27e48121741189",
    "r1_expires_in": 1800
}
"""


class TaoBaoBackend(RemoteUserBackend):
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, user=None, **kwargs):
        """{u'state': [u''], u'code': [u'sVT2F1nZtnkVLaEnhKiy5gS832237']}"""

        if not request.path.endswith(settings.REDIRECT_URI):
            return None

        content = request.REQUEST
        code = content.get('code')
        state = content.get('state')

        params = {
            'client_id': settings.APPKEY,
            'client_secret': settings.APPSECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': urlparse.urljoin(settings.SITE_URL,
                                             settings.REDIRECT_URI),
            'state': state,
            'view': 'web'
        }

        try:
            req = urllib2.urlopen(settings.AUTHRIZE_TOKEN_URL, urllib.urlencode(params))
            top_parameters = json.loads(req.read())
        except Exception, exc:
            import logging
            logger = logging.getLogger('django.request')
            logger.error(exc.message + '400', exc_info=True)
            return None

        request.session['top_session'] = top_parameters['access_token']
        request.session['top_parameters'] = top_parameters
        top_parameters['ts'] = time.time()

        try:
            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        except ValueError:
            raise SiteProfileNotAvailable('app_label and model_name should'
                                          ' be separated by a dot in the AUTH_PROFILE_MODULE set'
                                          'ting')

        try:
            model = models.get_model(app_label, model_name)
            if model is None:
                raise SiteProfileNotAvailable('Unable to load the profile '
                                              'model, check AUTH_PROFILE_MODULE in your project sett'
                                              'ings')
        except (ImportError, ImproperlyConfigured):
            raise SiteProfileNotAvailable('ImportError, ImproperlyConfigured error')

        user_id = top_parameters['taobao_user_id']

        try:
            profile = model.objects.get(visitor_id=user_id, type__in=['', model.SHOP_TYPE_B, model.SHOP_TYPE_C])
            profile.top_session = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()

            if profile.user:
                if not profile.user.is_active:
                    profile.user.is_active = True
                    profile.user.save()
                return profile.user
            else:
                user = model.getSystemOAUser()
                profile.user = user
                profile.save()
                return user

        except model.DoesNotExist:
            profile = model.getOrCreateSeller(user_id)
            profile.top_session = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
