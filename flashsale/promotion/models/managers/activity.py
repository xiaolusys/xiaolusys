# coding=utf-8
import datetime
from core.managers import BaseManager

import logging

logger = logging.getLogger(__name__)


class ActivityManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def default_activities(self):
        # type: () -> List[ActivityEntry]
        """默认返回活动
        """
        return self.get_queryset().filter(is_active=True,
                                          end_time__gte=datetime.datetime.now()) \
            .exclude(act_type__in=(self.model.ACT_MAMA, self.model.ACT_BRAND)) \
            .order_by('-order_val', '-modified')

    def effect_activities(self, time=None):
        # type: (Optional[datetime.datetime]) -> List[ActivityEntry]
        """有效活动
        """
        if time is None:
            time = datetime.datetime.now()
        return self.get_queryset().filter(is_active=True,
                                          start_time__lte=time,
                                          end_time__gte=time).order_by('-order_val', '-modified')

    def mama_effect_activities(self):
        # type: () -> List[ActivityEntry]
        """妈妈有效活动
        """
        self.effect_activities().filter(act_type=self.model.ACT_MAMA)

    def sale_home_page_activities(self):
        # type: () -> List[ActivityEntry]
        """特卖首页活动
        """
        self.effect_activities().exclude(act_type__in=(self.model.ACT_MAMA,
                                                       self.model.ACT_BRAND))
