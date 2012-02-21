from django.db import models
from django.contrib.auth.models import User
from auth.utils import verifySignature,decodeBase64String,parse_urlparams
from django.conf import settings
from auth import apis

import logging
logger = logging.getLogger('taobao.auth')


class TaoBaoBackend:
    supports_anonymous_user = False
    supports_object_permissions = False

    def authenticate(self, request, user=None):

        top_session = request.GET.get('top_session',None)
        if not top_session:
            top_session = request.session.get('top_session',None)
            top_parameters = request.session.get('top_parameters',None)
            if not (top_session and top_parameters):
                return None
        else:
            top_appkey = request.GET.get('top_appkey',None)
            top_parameters = request.GET.get('top_parameters',None)
            top_sign = request.GET.get('top_sign',None)

            basestring = '%s%s%s%s'%(top_appkey,top_parameters,top_session,settings.APPSECRET)

            sign_result = verifySignature(basestring,top_sign)

            if not sign_result:
                return None

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
            raise SiteProfileNotAvailable('ImportError, ImproperlyConfigured error')

        top_parameters = request.session.get('top_parameters')

        visitor_id = top_parameters['visitor_id']

        try:
            profile = model.objects.get(visitor_id=visitor_id)

            if profile.user:
                if not profile.user.is_active:
                    profile.user.is_active = True
                    profile.user.save()
                return profile.user
            else:
                user = User.objects.create(username=visitor_id,is_active=True)
                profile.user = user
                profile.save()
                return user
        except model.DoesNotExist:
            user = User.objects.create(username=visitor_id, is_active=True)
            model.objects.create(user=user, visitor_id=visitor_id)

            return user


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except:
            return None
  
