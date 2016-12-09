# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool
from datetime import datetime
from django.conf import settings
from shopapp.weixin.apis import WeiXinAPI
from shopapp.weixin.models import WeixinFans


def main():
    next_openid = ''

    count = 0
    t1 = datetime.now()
    add_count = 0
    while 1:
        appkey = settings.WX_PUB_APPID
        wxapi = WeiXinAPI()
        wxapi.setAccountId(appKey=appkey)
        json = wxapi.getFollowersID(next_openid=next_openid)
        next_openid = json.get('next_openid', None)
        openids = json.get('data', {}).get('openid', [])

        def worker(openid):
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
            # print user_info['nickname']

        pool = Pool(5)

        for i, openid in enumerate(openids):
            count += 1
            if count % 100 == 0:
                print count, add_count, (datetime.now() - t1).seconds

            fans = WeixinFans.objects.filter(app_key=appkey, openid=openid).first()
            if not fans:
                add_count += 1
                pool.spawn(worker, openid)
        pool.join()

        if not next_openid:
            break


if __name__ == '__main__':
    main()
