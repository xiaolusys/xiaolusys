# coding=utf-8
CARRY_IN_DEFAULT_DESC = '{0}'
CARRY_LOG_CLK_DESC = ['哇！好厉害，今天又有{0}点击您的链接,收益{1}', '大王，今天有来了{0}点击您的链接,收益{1}']
CARRY_LOG_SHOP_DESC = ['哇！好厉害，今天又有{0}个订单,收益{1}', '大王，今天有来了{0}订单,收益{1}']
CARRY_LOG_AGENCY_SUBSIDY = ['真棒,您招募的{0}专属又带来收益了,收益{1}', '大王，{0}专属为您贡献了补贴,收益{1},太开心了']
CARRY_OUT_DES = '{0}'

# 妈妈二维码分享图片存储路径
MAMA_LINK_FILEPATH = '/qrcode/xiaolumm/mm-{mm_linkid}.jpg'
# 妈妈专属链接
MAMA_SHARE_LINK = '{site_url}m/{mm_linkid}/'

APP_DOWNLOAD_URL = 'http://m.xiaolumeimei.com/sale/promotion/appdownload/'

PERSONAL_TARGET_STAGE = [
    (0, 30, 100),
    (130, 130, 200),
    (130, 230, 300),
    (230, 330, 400),
    (330, 430, 500),
    (430, 500, 600),
    (500, 600, 720),
    (600, 700, 840),
    (700, 800, 960),
]

PERSONAL_TARGET_STAGE.reverse()
PERSONAL_TARGET_AWARD_RATE = 0.15

GROUP_TARGET_STAGE = [
    (0, 800, 1000),
    (800, 1600, 2000),
    (1600, 2400, 3000),
    (2400, 3200, 4000)
]
GROUP_TARGET_STAGE.reverse()
GROUP_TARGET_AWARD_RATE = 0.05