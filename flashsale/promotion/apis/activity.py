# coding=utf-8
__ALL__ = [
    'get_default_activity',
    'get_activity_by_id',
    'get_effect_activitys',
    'get_mama_effect_activities'
]
import datetime
from ..models import ActivityEntry


def get_activity_by_id(id):
    # type: (int) -> ActivityEntry
    return ActivityEntry.objects.get(id=id)


def get_default_activity():
    # type: () -> Optional[ActivityEntry]
    """获取默认有效的活动（排除了代理活动　和　品牌专场）
    """
    return ActivityEntry.objects.filter(is_active=True,
                                        end_time__gte=datetime.datetime.now()) \
        .exclude(act_type__in=(ActivityEntry.ACT_MAMA, ActivityEntry.ACT_BRAND)) \
        .order_by('-order_val', '-modified').first()


def get_effect_activitys(time=None):
    # type: (datetime.datetime) -> List[ActivityEntry]
    """ 根据时间获取活动列表
    """
    if time is None:
        time = datetime.datetime.now()
    return ActivityEntry.objects.filter(is_active=True,
                                        start_time__lte=time,
                                        end_time__gte=time).order_by('-order_val', '-modified')


def get_mama_effect_activities():
    # type: () -> List[ActivityEntry]
    """获取有效的妈妈活动列表
    """
    return get_effect_activitys().filter(act_type=ActivityEntry.ACT_MAMA)


def get_landing_effect_activitys():
    # type: () -> List[ActivityEntry]
    """ 根据时间获取活动列表app首页展示 """
    return get_effect_activitys().exclude(act_type__in=(ActivityEntry.ACT_MAMA,
                                                        ActivityEntry.ACT_BRAND))

