# coding=utf-8
__ALL__ = [
    'get_nine_pic_advertisement_by_id',
    'get_nine_pic_advertisements_by_ids',
    'NinePicAdvertisement',
]


def get_nine_pic_advertisement_by_id(nine_pic_id):
    # type: (int) -> NinePicAdver
    from flashsale.xiaolumm.models import NinePicAdver

    return NinePicAdver.objects.get(id=nine_pic_id)


def get_nine_pic_advertisements_by_ids(ids):
    # type: (List[int]) -> List[NinePicAdver]
    from flashsale.xiaolumm.models import NinePicAdver

    return NinePicAdver.objects.filter(id__in=ids)


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

    @classmethod
    def create(cls, *args, **kwargs):
        # type: (text_type, text_type, datetime.datetime,
        # Optional[List[text_type]], text_type, int, Optional[int], bool, text_type) -> NinePicAdvertisement
        from flashsale.xiaolumm.models import NinePicAdver

        # 必须参数
        auther = kwargs['auther']
        title = kwargs['title']
        start_time = kwargs['start_time']

        pic_arry = kwargs.get('pic_arry') or None
        description = kwargs.get('description') or ''
        advertisement_type = kwargs.get('advertisement_type') or 9
        category_id = kwargs.get('category_id') or None
        is_pushed = kwargs.get('is_pushed') or False
        redirect_url = kwargs.get('redirect_url') or ''

        return NinePicAdver.create(auther, title, start_time,
                                   pic_arry=pic_arry, description=description, advertisement_type=advertisement_type,
                                   category_id=category_id, is_pushed=is_pushed, redirect_url=redirect_url)
