# encoding=utf8
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from shopapp.weixin.weixin_apis import WeiXinAPI
from shopapp.weixin.models_base import WeixinFans


class Command(BaseCommand):
    def handle(self, *args, **options):
        appkey = settings.WXPAY_APPID  # 小鹿美美公众号

        wxapi = WeiXinAPI()
        wxapi.setAccountId(appKey=appkey)
        json = wxapi.getFollowersID()
        openids = json.get('data', {}).get('openid', [])

        for openid in openids[:100]:
            fans = WeixinFans.objects.filter(app_key=appkey, openid=openid).first()
            if not fans:
                user_info = wxapi.getCustomerInfo(openid)

                unionid = user_info.get('unionid', '')
                subscribe = True if user_info.get('subscribe', False) else False
                subscribe_time = datetime.fromtimestamp(user_info['subscribe_time']) if subscribe else None

                fans = WeixinFans()
                fans.openid = openid
                fans.app_key = appkey
                fans.unionid = unionid
                fans.subscribe = subscribe
                fans.subscribe_time = subscribe_time
                fans.save()

                print '==>', 'insert ', openid, unionid, subscribe
            else:
                print '==>', 'has ', openid
