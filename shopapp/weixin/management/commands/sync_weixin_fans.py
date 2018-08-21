# encoding=utf8
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from shopapp.weixin.apis import WeiXinAPI
from shopapp.weixin.models import WeixinFans


class Command(BaseCommand):
    def sync_fans(self, appkey):
        num = 0
        next_openid = ''

        while 1:
            wxapi = WeiXinAPI()
            wxapi.setAccountId(appKey=appkey)
            json = wxapi.getFollowersID(next_openid=next_openid)
            openids = json.get('data', {}).get('openid', [])
            next_openid = json.get('next_openid', None)
            total = json.get('total', None)

            openids_in_db = WeixinFans.objects.filter(app_key=appkey).values('openid')
            openids_in_db = [x['openid'] for x in openids_in_db]

            openids = [x for x in openids if x not in openids_in_db]

            for openid in openids:
                fans = WeixinFans.objects.filter(app_key=appkey, openid=openid).first()
                if not fans:
                    try:
                        user_info = wxapi.getCustomerInfo(openid)
                    except Exception:
                        wxapi = WeiXinAPI()
                        wxapi.setAccountId(appKey=appkey)
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
                num = num + 1

                if num % 100 == 0:
                    print '%s/%s' % (num, total)

            if not next_openid:
                break

    def handle(self, *args, **options):
        appkeys = [
            # settings.WX_PUB_APPID,  # 小鹿美美公众号
            settings.WEIXIN_APPID,  # 小鹿特卖
        ]

        for appkey in appkeys:
            self.sync_fans(appkey)
