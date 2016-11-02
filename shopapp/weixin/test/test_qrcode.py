# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.local_settings")
from shopapp.weixin.utils import generate_colorful_qrcode


def test_main():
    params = {
      "background_url": "http://7xkyoy.com1.z0.glb.clouddn.com/mama_referal_base12.jpg",
      "text": {
        "content": u"你好是我是s小鹿的ss爸d爸k",
        "font_size": 36,
        "y": 174,
        "color": "#f1c40f"
      },
      "avatar": {
        "url": "http://wx.qlogo.cn/mmopen/Q3auHgzwzM770QstXrQ96q9NWztxnufE4C4o8vtNTQPUGbtlBXqyRicm9d4Wx7oUnFp2q3lUWkkDMkofZhqicOdRUraicZDC9yic91h6ksPiaBGI/0",
        "size": 120,
        "x": 50,
        "y": 30
      },
      "qrcode": {
        # "url": "http://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=gQH47joAAAAAAAAAASxodHRwOi8vd2VpeGluLnFxLmNvbS9xL2taZ2Z3TVRtNzJXV1Brb3ZhYmJJAAIEZ23sUwMEmm3sUw==",
        'text': 'haha',
        "img": "http://wx.qlogo.cn/mmopen/Q3auHgzwzM770QstXrQ96q9NWztxnufE4C4o8vtNTQPUGbtlBXqyRicm9d4Wx7oUnFp2q3lUWkkDMkofZhqicOdRUraicZDC9yic91h6ksPiaBGI/0",
        "size": 430,
        "x": 85,
        "y": 409
      }
    }
    generate_colorful_qrcode(params)

if __name__ == '__main__':
    import django
    from datetime import datetime
    django.setup()

    t1 = datetime.now()
    # for i in range(100):
    test_main()
        # print i
    # t2 = datetime.now()
    print (t2-t1).seconds
