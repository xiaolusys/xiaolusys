import pingpp

from django.conf import settings

pingpp.api_key = settings.PINGPP_APPKEY


def redpack(order_no):
    """ 
    {
      "body": "Your Body", 
      "object": "red_envelope", 
      "description": "Your Description", 
      "order_no": "111112313413413666", 
      "extra": {
        "nick_name": "Nick Name", 
        "send_name": "Send Name"
      }, 
      "app": "app_LOOajDn9u9WDjfHa", 
      "livemode": false, 
      "paid": true, 
      "created": 1430644197, 
      "currency": "cny", 
      "amount": 100, 
      "recipient": "our5huIOSuFF5FdojFMFNP5HNOmA", 
      "id": "red_0aXTiP9C4iTSKGWPqPynLmrH", 
      "channel": "wx_pub", 
      "subject": "Your Subject"
    }
    """
    redenvelope = pingpp.RedEnvelope.create(
        order_no=order_no,
        channel='wx_pub',
        amount=100,
        subject='Your Subject',
        body='Your Body',
        currency='cny',
        app=dict(id=settings.PINGPP_APPID),
        extra=dict(nick_name='Nick Name', send_name='Send Name'),
        recipient='our5huIOSuFF5FdojFMFNP5HNOmA',
        description='Your Description'
    )

    print 'appkey,secret:' + settings.PINGPP_APPID, settings.PINGPP_APPKEY
    print 'red pack:', redenvelope
