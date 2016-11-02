import time
import json
import urllib
import urllib2
import urlparse
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.backends import RemoteUserBackend
from django.conf import settings
from shopback.users.models import User as Seller
from auth import apis

import logging

logger = logging.getLogger('django.request')

JINGDONG_PREFFIX = 'jd'


class JingDongBackend(RemoteUserBackend):
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, user=None, **kwargs):
        """{u'state': [u''], u'code': [u'sVT2F1nZtnkVLaEnhKiy5gS832237']}"""

        if not request.path.endswith(settings.JD_REDIRECT_URI):
            return None

        content = request.REQUEST
        code = content.get('code')
        state = content.get('state')

        params = {
            'client_id': settings.JD_APP_KEY,
            'client_secret': settings.JD_APP_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': urlparse.urljoin(settings.SITE_URL,
                                             settings.JD_REDIRECT_URI),
            'state': state,
            'scope': 'read'
        }

        try:
            req = urllib2.urlopen(settings.JD_AUTHRIZE_TOKEN_URL,
                                  urllib.urlencode(params))
            resp = req.read()
            top_parameters = json.loads(resp.decode('gbk'))
            if top_parameters.get('code', None):
                return None
        except Exception, exc:
            logger.error('jingdong autherize token error:%s' % exc.message, exc_info=True)
            return None

        request.session['top_session'] = top_parameters['access_token']
        request.session['top_parameters'] = top_parameters
        top_parameters['time'] = int(time.time() * 1000)

        try:
            app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
        except ValueError:
            raise SiteProfileNotAvailable('app_label and model_name should'
                                          ' be separated by a dot in the AUTH_PROFILE_MODULE '
                                          'setting')

        try:
            model = models.get_model(app_label, model_name)
            if model is None:
                raise SiteProfileNotAvailable('Unable to load the profile '
                                              'model, check AUTH_PROFILE_MODULE in your'
                                              ' project settings')
        except (ImportError, ImproperlyConfigured):
            raise SiteProfileNotAvailable('ImportError, ImproperlyConfigured error')

        user = Seller.getSystemOAUser()
        try:
            profile = model.objects.get(user=user,
                                        type=model.SHOP_TYPE_JD)
            profile.top_session = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()

            if not profile.user.is_active:
                profile.user.is_active = True
                profile.user.save()
            return profile.user

        except model.DoesNotExist:
            profile, state = model.objects.get_or_create(user=user,
                                                         type=model.SHOP_TYPE_JD)
            profile.top_session = top_parameters['access_token']
            profile.top_parameters = json.dumps(top_parameters)
            profile.save()
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
