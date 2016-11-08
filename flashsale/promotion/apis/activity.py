# coding=utf-8
__ALL__ = [
    'get_default_activity',
    'get_activity_by_id',
    'get_effect_activitys',
    'get_mama_effect_activities',
    'get_landing_effect_activitys',
    'create_activity',
    'update_activity',
    'get_activity_pro_by_id',
    'get_activity_pros_by_activity_id',
    'create_activity_pro',
    'create_activity_pros_by_schedule_id',
    'update_activity_pro'
]
import datetime
from ..models import ActivityEntry, ActivityProduct
from ..deps import get_schedule_products_by_schedule_id


def get_activity_by_id(id):
    # type: (int) -> ActivityEntry
    return ActivityEntry.objects.get(id=id)


def get_default_activity():
    # type: () -> Optional[ActivityEntry]
    """获取默认有效的活动（排除了代理活动　和　品牌专场）
    """
    return ActivityEntry.objects.default_activities().first()


def get_effect_activities(time=None):
    # type: (datetime.datetime) -> List[ActivityEntry]
    """ 根据时间获取活动列表
    """
    return ActivityEntry.objects.effect_activities(time)


def get_mama_effect_activities():
    # type: () -> List[ActivityEntry]
    """获取有效的妈妈活动列表
    """
    return ActivityEntry.objects.mama_effect_activities()


def get_landing_effect_activities():
    # type: () -> List[ActivityEntry]
    """ 根据时间获取活动列表app首页展示 """
    return ActivityEntry.objects.sale_home_page_activities()


def _validate_start_end_time(start_time, end_time):
    # type: (datetime.datetime, datetime.datetime) -> None
    """时间校验
    """
    now = datetime.datetime.now()
    if not start_time < end_time:
        raise Exception(u'活动开始和结束时间设置错误!')
    if not now < end_time:
        raise Exception(u'活动结束时间应该大于当前时间!')
    return


class Activity(object):  # 特卖商城活动(pay.models.ActivityEntry)
    def __init__(self, title, act_type, start_time, end_time,
                 act_img='', act_logo='', act_link='', mask_link='', act_applink='', share_icon='', share_link='',
                 order_val=0, extras='', is_active=False, login_required=False, act_desc=''):
        self.title = title  # 活动/品牌名称
        self.act_type = act_type  # 活动类型
        self.start_time = start_time  # 结束时间
        self.end_time = end_time  # 开始时间
        self.act_img = act_img  # 活动入口图片
        self.act_logo = act_logo  # 品牌LOGO
        self.act_link = act_link  # 活动链接
        self.mask_link = mask_link  # 活动弹窗提示图
        self.act_applink = act_applink  # 活动APP协议链接
        self.share_icon = share_icon  # 活动分享图片
        self.share_link = share_link  # 活动分享链接
        self.order_val = order_val  # 排序值
        self.extras = extras  # 活动数据
        self.is_active = is_active  # 上线
        self.login_required = login_required  # 需要登陆
        self.act_desc = act_desc  # 活动描述

    def save(self, id=None):
        # type: (Optional[int]) -> ActivityEntry
        """保存到活动记录到数据库
        """
        from flashsale.promotion.models import ActivityEntry

        if id is not None:
            activity = get_activity_by_id(id)
            for k, v in activity.__dict__.iteritems():
                if hasattr(activity, k) and getattr(self, k) != v:
                    setattr(activity, k, getattr(self, k))
            activity.save()
        else:
            activity = ActivityEntry(
                title=self.title,
                act_type=self.act_type,
                start_time=self.start_time,
                end_time=self.end_time,
                act_img=self.act_img,
                act_logo=self.act_logo,
                act_link=self.act_link,
                mask_link=self.mask_link,
                act_applink=self.act_applink,
                share_icon=self.share_icon,
                share_link=self.share_link,
                order_val=self.order_val,
                extras=self.extras,
                is_active=self.is_active,
                login_required=self.login_required,
                act_desc=self.act_desc,
            )
            activity.save()
        return activity


def create_activity(title, act_type, start_time, end_time, **kwargs):
    # type: (text_type, text_type, datetime.datetime, datetime.datetime, **Any) -> ActivityEntry
    """创建活动
    """
    if act_type == ActivityEntry.ACT_TOPIC and kwargs.has_key('act_link'):
        # http://m.xiaolumeimei.com/mall/activity/topTen/model/2?id=264 # 专题类型活动链接固定格式
        kwargs.pop('act_link')  # 去除传来的act_link 如果有的话
    activity = Activity(title=title,
                        act_type=act_type,
                        start_time=start_time,
                        end_time=end_time)
    for k, v in kwargs.iteritems():
        if hasattr(activity, k) and getattr(activity, k) != v:
            setattr(activity, k, v)
    _validate_start_end_time(start_time, end_time)
    activity = activity.save()
    activity.act_link = 'http://m.xiaolumeimei.com/mall/activity/topTen/model/2?id={0}'.format(activity.id)
    activity.save(id=activity.id)
    return activity


def update_activity(id, **kwargs):
    # type: (int, **Any) -> ActivityEntry
    """更新活动
    """
    activity = get_activity_by_id(id=id)
    start_time, end_time = kwargs.get('start_time'), kwargs.get('end_time')
    act_type = kwargs.get('act_type')
    if act_type == ActivityEntry.ACT_TOPIC and kwargs.has_key('act_link'):
        kwargs.pop('act_link')  # 在创建的时候已经填写过act_link了不需要重新填写
    for k, v in kwargs.iteritems():
        if hasattr(activity, k) and getattr(activity, k) != v:
            setattr(activity, k, v)
    _validate_start_end_time(start_time, end_time)
    activity.save()
    return activity


def get_activity_pro_by_id(id):
    # type: (int) -> ActivityProduct
    return ActivityProduct.objects.get(id=id)


def get_activity_pros_by_activity_id(activity_id):
    # type: (int) -> List[ActivityProduct]
    """根据活动id获取相关的产品
    """
    return ActivityProduct.objects.pros_by_activity_id(activity_id)


class ActivityPro(object):  # 活动更随的产品（包含图片）
    def __init__(self, activity_id, product_img, location_id=1, product_name='', pic_type=6, model_id=0, jump_url=''):
        self.activity_id = activity_id
        self.product_name = product_name
        self.product_img = product_img
        self.pic_type = pic_type
        self.location_id = location_id
        self.model_id = model_id
        self.jump_url = jump_url

    def save(self, id=None):
        if id is None:
            ap = ActivityProduct(
                activity=self.activity_id,
                model_id=self.model_id,
                product_name=self.product_name,
                product_img=self.product_img,
                location_id=self.location_id,
                pic_type=self.pic_type,
                jump_url=self.jump_url,
            )
            ap.save()
        else:
            ap = get_activity_pro_by_id(id)
            for k, v in ap.__dict__.iteritems():
                if hasattr(ap, k) and getattr(self, k) != v:
                    setattr(ap, k, getattr(self, k))
            ap.save()
        return ap


def create_activity_pro(activity_id, product_img, **kwargs):
    # type: (int, text_type, **Any)
    """创建活动商品
    """
    ap = ActivityPro(
        activity_id=activity_id,
        product_img=product_img,
    )
    for k, v in kwargs.iteritems():
        if hasattr(ap, k) and getattr(ap, k) != v:
            setattr(ap, k, v)
    ap = ap.save()
    return ap


def update_activity_pro(id, **kwargs):
    # type: () -> ActivityProduct
    """更新活动产品
    """
    ap = get_activity_pro_by_id(id)
    for k, v in kwargs.iteritems():
        if hasattr(ap, k) and getattr(ap, k) != v:
            setattr(ap, k, v)
    ap = ap.save()
    return ap


def create_activity_pros_by_schedule_id(activity_id, schedule_id):
    # type: (int, int) -> List[ActivityProduct]
    """更具活动id和排期id创建活动产品
    """
    activity = get_activity_by_id(activity_id)
    schedule_pros = get_schedule_products_by_schedule_id(int(schedule_id))
    aps = []
    model_ids = [i['model_id'] for i in activity.activity_products.values('model_id')]
    for pro in schedule_pros:
        location_id = 2
        modelproduct = pro.modelproduct
        if modelproduct and modelproduct.id not in model_ids:  # 存在款式并且没有设置在本活动中则添加到本活动中
            kwargs = {
                'product_name': modelproduct.name,
                'model_id': modelproduct.id,
                'location_id': location_id,
            }
            ap = create_activity_pro(activity_id, modelproduct.head_img_url, **kwargs)
            aps.append(ap)
        location_id += 1
    return aps

