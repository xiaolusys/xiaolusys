import urllib
import urllib2
from django.db import models
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.utils import simplejson as json
from auth.utils import verifySignature,decodeBase64String,parse_urlparams
from django.conf import settings
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')

""" top_parameters:
{'visitor_nick': 'honey', 'expires_in': '86400', 'visitor_id': '180023275', 'ts': '1325846382971',
'iframe': '1', 're_expires_in': '15552000', 'refresh_token': '6100a20adf4b9a6c361ef23f39371de459a2cbfd29627d7180023275'}
"""

class TaoBaoBackend:
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, user=None):
        top_session = request.GET.get('top_session',None)
        if not top_session:
            top_session = request.session.get('top_session',None)
            top_parameters = request.session.get('top_parameters',None)
            if not (top_session and top_parameters):
                raise Http500
        else:
            top_appkey = request.GET.get('top_appkey',None)
            top_parameters = request.GET.get('top_parameters',None)
            top_sign = request.GET.get('top_sign',None)

            basestring = '%s%s%s%s'%(top_appkey,top_parameters,top_session,settings.APPSECRET)

            sign_result = verifySignature(basestring,top_sign)

            if not sign_result:
                raise Http500
            else:
                request.session['top_appkey'] = top_appkey
                request.session['top_session'] = top_session

                decodestring = decodeBase64String(top_parameters)
                params = parse_urlparams(decodestring)

                request.session['top_parameters'] = params

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
            raise SiteProfileNotAvailable

        user_id = request['top_parameters']['visitor_id']
        try:
            user = model.objects.get(username=user_id)
        except model.DoesNotExist:
            user = User.objects.create(username=user_id, is_active=True)
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
  