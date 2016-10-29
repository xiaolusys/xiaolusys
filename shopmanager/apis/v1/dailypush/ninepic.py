# coding=utf-8
__ALL__ = [
    'get_nine_pic_advertisement_by_id',
    'get_nine_pic_advertisements_by_ids',
    'create_nine_pic_advertisement',
    'delete_nine_pic_advertisement_by_id',
    'update_nine_pic_advertisement_by_id',
    'get_nine_pic_descriptions_by_modelids',
    'NinePicAdvertisement',
]
import re
import datetime
import logging

logger = logging.getLogger(__name__)


def _init_time(assign_date=None):
    # type: (Optional[datetime.date]) -> datetime.datetime
    now = datetime.datetime.now() if assign_date is None else datetime.datetime(assign_date.year,
                                                                                assign_date.month,
                                                                                assign_date.day, 0, 0)
    return datetime.datetime(now.year, now.month, now.day, 0, 0, 0)


def _calculate_create_assign_turns_num(assign_datetime=None):
    # type: (Optional[datetime.datetime]) -> int
    from flashsale.xiaolumm.models import NinePicAdver

    init_time = _init_time(assign_datetime.date())
    end_time = datetime.datetime(init_time.year, init_time.month, init_time.day, 23, 59, 59)
    return NinePicAdver.objects.filter(start_time__gte=init_time, start_time__lte=end_time).count()


def _resort_turns_num(date):
    # type: (datetime.date) -> None
    """指定日期的九张图推广轮数重新排序
    """
    from flashsale.xiaolumm.models import NinePicAdver

    init_time = _init_time(date)
    end_time = datetime.datetime(init_time.year, init_time.month, init_time.day, 23, 59, 59)
    count = 1
    for ninepic in NinePicAdver.objects.filter(start_time__gte=init_time,
                                               start_time__lte=end_time).order_by('start_time'):
        ninepic.turns_num = count
        ninepic.save(update_fields=['turns_num'])
        count += 1
    return


def get_nine_pic_advertisement_by_id(nine_pic_id):
    # type: (int) -> NinePicAdver
    from flashsale.xiaolumm.models import NinePicAdver

    return NinePicAdver.objects.get(id=nine_pic_id)


def get_nine_pic_advertisements_by_ids(ids):
    # type: (List[int]) -> List[NinePicAdver]
    from flashsale.xiaolumm.models import NinePicAdver

    return NinePicAdver.objects.filter(id__in=ids)


def create_nine_pic_advertisement(author, title, start_time, **kwargs):
    # type: (text_type, text_type, datetime.datetime, *Any, **Any) -> NinePicAdver
    from flashsale.xiaolumm.models import NinePicAdver

    pic_arry = kwargs.get('pic_arry') or None
    description = kwargs.get('description') or ''
    advertisement_type = kwargs.get('advertisement_type') or 9
    sale_category_id = kwargs.get('sale_category') or None
    is_pushed = kwargs.get('is_pushed') or False
    redirect_url = kwargs.get('redirect_url') or ''
    detail_modelids = kwargs.get('detail_modelids') or ''
    memo = kwargs.get('memo') or ''
    turns_num = _calculate_create_assign_turns_num(start_time)  # 轮数
    verify_turns_num = NinePicAdver.objects.filter(start_time__gte=_init_time(start_time.date()),
                                                   start_time__lt=start_time).count()
    n = NinePicAdver(auther=author,
                     title=title,
                     start_time=start_time,
                     description=description,
                     cate_gory=advertisement_type,
                     sale_category_id=sale_category_id,
                     pic_arry=pic_arry,
                     turns_num=turns_num + 1,
                     is_pushed=is_pushed,
                     detail_modelids=detail_modelids,
                     redirect_url=redirect_url,
                     memo=memo)
    n.save()
    if turns_num != verify_turns_num:  # 轮数不想等则重新排序
        _resort_turns_num(start_time.date)
    return n


def delete_nine_pic_advertisement_by_id(id):
    # type: () -> bool
    """删除记录
    1. 删除记录
    2. 重新排轮数
    """
    ninepic = get_nine_pic_advertisement_by_id(id)
    date = ninepic.start_time.date()
    ninepic.delete()
    _resort_turns_num(date)
    return True


def update_nine_pic_advertisement_by_id(id, **kwargs):
    # type: (int, **Any) -> NinePicAdver
    """更新记录
    １. 如果有时间变化，则重新排轮数
    """
    ninepic = get_nine_pic_advertisement_by_id(id)
    if kwargs.has_key('turns_num'):  # 不更新传入的turns_num
        kwargs.pop('turns_num')
    if kwargs.has_key('sale_category'):
        kwargs.update({'sale_category_id': kwargs.pop('sale_category')})
    if not kwargs.has_key('start_time'):  # 没有重新设置时间则不去更新时间和　turns_num
        kwargs.update({'turns_num': ninepic.turns_num})
    else:
        start_time = datetime.datetime.strptime(kwargs.get('start_time'), '%Y-%m-%d %H:%M:%S')
        old_start_time_date = ninepic.start_time.date()
        if old_start_time_date != start_time.date():  # 不相等则都重新排序修改　轮数
            _resort_turns_num(old_start_time_date)
        _resort_turns_num(start_time.date())
    for k, v in kwargs.iteritems():
        if hasattr(ninepic, k) and getattr(ninepic, k) != v:
            setattr(ninepic, k, v)
    ninepic.save()
    return ninepic


def get_nine_pic_descriptions_by_modelids(modelids):
    # type: (List[int]) -> List[Dict[str, Any]]
    from flashsale.xiaolumm.models.models_advertis import NinePicAdver

    descriptions = []
    for modelid in modelids:
        x = r'(,|^)\s*' + str(modelid) + r'\s*(,|$)'
        descriptions.extend(
            NinePicAdver.objects.filter(detail_modelids__regex=x).values('id',
                                                                         'detail_modelids',
                                                                         'description'))
    return descriptions


class NinePicAdvertisement(object):
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.auther = kwargs['auther']
        self.title = kwargs['title']
        self.description = ''
        self.cate_gory = 9  # 九张图
        self.sale_category_id = None
        self.pic_arry = []
        self.start_time = kwargs['start_time']
        self.turns_num = kwargs['turns_num']
        self.is_pushed = False
        self.save_times = 0
        self.share_times = 0
        self.redirect_url = ''  # 跳转链接
        self.detail_modelids = ''
        self.memo = ''
