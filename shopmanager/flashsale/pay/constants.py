# coding=utf-8

WX         = 'wx'
ALIPAY     = 'alipay'
WX_PUB     = 'wx_pub'
ALIPAY_WAP = 'alipay_wap'
UPMP_WAP   = 'upmp_wap'
WALLET     = 'wallet'

CHANNEL_CHOICES = (
    (WALLET,u'小鹿钱包'),
    (WX,u'微信APP'),
    (ALIPAY,u'支付宝APP'),
    (WX_PUB,u'微支付'),
    (ALIPAY_WAP,u'支付宝'),
    (UPMP_WAP,u'银联'),
)

MALL_LOGIN_URL = '/pages/denglu.html'
MAIL_PAY_SUCCESS_URL = '/pages/zhifucg.html'
MAIL_PAY_CANCEL_URL = '/pages/zhifucg.html'

COUPON_ID_FOR_20160223_AWARD = 22

ENVELOP_BODY = u'一份耕耘，一份收获，谢谢你的努力！'
ENVELOP_CASHOUT_DESC = u"用户编号:{0},提现前:{1}"

IS_USERBUDGET_COULD_CASHOUT = 1  # 等于１的时候允许提现

CHILD_CID_LIST = [12, 13, 14, 15, 16, 17, 23, 25, 26]
FEMALE_CID_LIST = [18, 19, 20, 21, 22, 24, 27]

