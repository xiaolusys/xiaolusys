# coding: utf-8

from functools import wraps
import json
import hashlib
import requests

from django.conf import settings
from django.core.cache import get_cache

from .decorators import mask, retry


class MiPush(object):
    # 全推
    BROADCAST_URL = 'https://api.xmpush.xiaomi.com/v2/message/all'
    # 按照标签推送
    TOPIC_URL = 'https://api.xmpush.xiaomi.com/v2/message/topic'
    # 按照account推送
    ACCOUNT_URL = 'https://api.xmpush.xiaomi.com/v2/message/user_account'
    # 按照regid推送
    REGID_URL = 'https://api.xmpush.xiaomi.com/v2/message/regid'
    # 设置标签
    SUBSCRIBE_BY_REGID_URL = 'https://api.xmpush.xiaomi.com/v2/topic/subscribe'
    # 取消标签
    UNSUBSCRIBE_BY_REGID_URL = 'https://api.xmpush.xiaomi.com/v2/topic/unsubscribe'

    # app_secret
    IOS_APP_SECRET = 'UN+ohC2HYHUlDECbvVKefA=='
    ANDROID_APP_SECRET = '5jZErBkrZ+Wl3ASRhJOIXg=='
    RESTRICTED_PACKAGE_NAME = 'com.jimei.xlmm'

    # notify_id
    MAX_TOPIC_NID = 1 << 8
    MAX_ACCOUNT_NID = 1 << 8
    MAX_REGISTRATION_NID = 1 << 8
    MAX_ALL_NID = 1 << 8

    # cache相关
    CACHE_INTERVAL = 7200
    ALL_CACHE_KEY = 'mipush-all'
    TOPIC_CACHE_KEY = 'mipush-topic'
    ACCOUNT_CACHE_KEY_TPL = 'mipush-account-%d'
    REGISTRATION_CACHE_KEY_TPL= 'mipush-regid-%s'

    # 推送设置
    TIME_TO_LIVE = 8 * 3600 * 1000
    PASS_THROUGH = 0


    def __init__(self, platform='android'):
        self.platform = platform
        self.session = requests.Session()

        if platform == 'ios':
            self.app_secret = self.IOS_APP_SECRET
        else:
            self.app_secret = self.ANDROID_APP_SECRET
        self.headers = {
            'Authorization': 'key=%s' % self.app_secret,
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        self.session.headers.update(self.headers)

    def post(self, url, data):
        req = self.session.prepare_request(requests.Request('POST',
                                                            url,
                                                            data=data))
        return self.session.send(req, timeout=60.0)

    def get(self, url, data):
        req = self.session.prepare_request(requests.Request('GET',
                                                            url,
                                                            params=data))
        return self.session.send(req, timeout=60.0)

    @mask(1 << 10)
    def get_account_nid(self, customer_id):
        cache_key = self.ACCOUNT_CACHE_KEY_TPL % customer_id
        cache = get_cache('default')
        account_nid = cache.get(cache_key)
        if account_nid is None or account_nid >= self.MAX_ACCOUNT_NID:
            cache.set(cache_key, 1, self.CACHE_INTERVAL)
            return 1
        return cache.incr(cache_key)

    @mask(1 << 11)
    def get_registration_nid(self, regid):
        if len(regid) > 200:
            regid = hashlib.sha1(regid).hexdigest()
        cache_key = self.REGISTRATION_CACHE_KEY_TPL % regid
        cache = get_cache('default')
        registration_nid = cache.get(cache_key)

        if registration_nid is None or registration_nid >= self.MAX_REGISTRATION_NID:
            cache.set(cache_key, 1, self.CACHE_INTERVAL)
            return 1
        return cache.incr(cache_key)


    @mask(1 << 12)
    def get_topic_nid(self):
        cache = get_cache('default')
        topic_nid = cache.get(self.TOPIC_CACHE_KEY)
        if topic_nid is None or topic_nid >= self.MAX_TOPIC_NID:
            cache.set(self.TOPIC_CACHE_KEY, 1, self.CACHE_INTERVAL)
            return 1
        return cache.incr(self.TOPIC_CACHE_KEY)

    @mask(1 << 13)
    def get_all_nid(self):
        cache = get_cache('default')
        all_nid = cache.get(self.ALL_CACHE_KEY)
        if all_nid is None or all_nid >= self.MAX_ALL_NID:
            cache.set(self.ALL_CACHE_KEY, 1, self.CACHE_INTERVAL)
            return 1
        return cache.incr(self.ALL_CACHE_KEY)

    def build(self,
              payload,
              title='',
              description='',
              notify_type=-1,
              notify_id=0,
              time_to_live=None,
              extra=None):
        if not time_to_live:
            time_to_live = self.TIME_TO_LIVE
        # common data
        data = {
            'description': description,
            'notify_type': notify_type,
            'notify_id': notify_id,
            'pass_through': self.PASS_THROUGH,
            'time_to_live': time_to_live
        }
        if self.platform == 'ios':
            data['extra.badge'] = 1
        else:
            data.update({
                'title': title,
                'restricted_package_name': self.RESTRICTED_PACKAGE_NAME,
                'payload': json.dumps(payload) if not isinstance(
                    payload, basestring) else payload
            })
        # set extra
        if extra and isinstance(extra, dict):
            for k, v in extra.iteritems():
                if isinstance(v, dict) and self.platform == 'ios':
                    v = json.dumps(v)
                data['extra.%s' % k] = v
        return data

    @retry()
    def push_to_account(self,
                        customer_id,
                        payload,
                        title='小鹿美美',
                        description='',
                        notify_type=-1,
                        notify_id=0,
                        time_to_send=None,
                        extra=None):
        if not notify_id:
            notify_id = self.get_account_nid(customer_id)
        data = self.build(payload,
                          title,
                          description,
                          notify_type,
                          notify_id,
                          time_to_send,
                          extra=extra)
        data['user_account'] = 'user-%d' % customer_id
        return self.post(self.ACCOUNT_URL, data)

    @retry()
    def push_to_regid(self, regid, payload, title='小鹿美美', description='', notify_type=1, notify_id=0, time_to_send=None, extra=None):
        if not notify_id:
            notify_id = self.get_registration_nid(regid)
        data = self.build(payload,
                          title,
                          description,
                          notify_type,
                          notify_id,
                          time_to_send,
                          extra=extra)
        data['registration_id'] = regid
        return self.post(self.REGID_URL, data)

    @retry()
    def push_to_topic(self,
                      topic,
                      payload,
                      title='小鹿美美',
                      description='',
                      notify_type=-1,
                      notify_id=0,
                      time_to_send=None,
                      extra=None):
        if not notify_id:
            notify_id = self.get_topic_nid()
        data = self.build(payload,
                          title,
                          description,
                          notify_type,
                          notify_id,
                          time_to_send,
                          extra=extra)
        data['topic'] = topic
        return self.post(self.TOPIC_URL, data)

    @retry()
    def push_to_all(self,
                    payload,
                    title='小鹿美美',
                    description='',
                    notify_type=1,
                    notify_id=0,
                    time_to_send=None,
                    extra=None):
        if not notify_id:
            notify_id = self.get_all_nid()
        data = self.build(payload,
                          title,
                          description,
                          notify_type,
                          notify_id,
                          time_to_send,
                          extra=extra)
        return self.post(self.BROADCAST_URL, data)

    @retry()
    def subscribe_by_regid(self, regid, topic):
        data = {
            'registration_id': regid,
            'topic': topic
        }
        return self.post(self.SUBSCRIBE_BY_REGID_URL, data)

    @retry()
    def unsubscribe_by_regid(self, regid, topic):
        data = {
            'registration_id': regid,
            'topic': topic
        }
        return self.post(self.UNSUBSCRIBE_BY_REGID_URL, data)


mipush_of_ios = MiPush('ios')
mipush_of_android = MiPush('android')
