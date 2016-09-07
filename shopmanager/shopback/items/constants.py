# coding: utf-8

from django.conf import settings

if settings.DEBUG:
    PAGE_SIZE = 3
else:
    PAGE_SIZE = 20

SALE_TYPES = (
    (1, u'0-50元'),
    (2, u'50-150元'),
    (3, u'150以上'),
    (4, u'引流款')
)

SCHEDULE_API_TYPE_PRICE = 1
SCHEDULE_API_TYPE_SECKILL = 2
SCHEDULE_API_TYPE_WATERMARK = 3
SCHEDULE_API_TYPE_STATUS = 5

#商城商品详情页
MALL_PRODUCT_TEMPLATE_URL = '/mall/product/details/{0}'

#商品资料sku排序位标
SKU_CONSTANTS_SORT_MAP = 'SMLXSXMXLXXL0A1B2C3D4E5F60708090951011213141516171819'+ ''.join([str(i) for i in range(20, 40)])


CATEGORY_CHILDREN  = '1'
CATEGORY_WEMON     = '2'
CATEGORY_HEALTH    = '3'
CATEGORY_ACCESSORY = '4'
CATEGORY_MUYING    = '5'
CATEGORY_BAGS      = '6'
CATEGORY_MEIZUANG  = '7'
CATEGORY_ACCESSOR  = '2-73'

MALL_PRODUCT_ENDCODE = '1'
MALL_PARENT_STARTCODE = '1'
MALL_CHILD_STARTCODE = '9'
MALL_FEMALE_STARTCODE = '8'

PROPERTY_NAMES = (
    ('model_code', u'商品编码'),
    ('material', u'商品材质'),
    ('fashion', u'流行元素'),
    ('shoulder', u'肩带款式'),
    ('color', u'可选颜色'),
    ('wash_instructions', u'洗涤说明'),
    ('wash_instroduce', u'洗涤说明'),
    ('qs_code', u'生产许可证'),
    ('qhby_code', u'产品标准号'),
    ('efficacy', u'产品功效'),
    ('suitofskin', u'适合肤质'),
    ('note', u'备注说明'),
    ('memo', u'备注说明'),
)

PROPERTY_KEYMAP = dict([(key[0], index) for index, key in enumerate(PROPERTY_NAMES)])



