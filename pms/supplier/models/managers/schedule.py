# coding=utf-8
import datetime
from django.db.models import Q

from core.managers import BaseManager


class ScheduleManager(BaseManager):
    def get_query_set(self):
        _super = super(BaseManager, self)
        if hasattr(_super, 'get_query_set'):
            return _super.get_query_set()
        return _super.get_queryset()

    get_queryset = get_query_set

    def future_schedules(self):
        # type: () -> List[SaleProductManage]
        """未来排期
        """
        today = datetime.date.today()
        return self.get_queryset().filter(sale_time__gte=today)

    def future_topic_schedules(self):
        # type: () -> List[SaleProductManage]
        """未来排期
        """
        return self.future_schedules().filter(schedule_type=self.model.SP_TOPIC)

    def activeable_topic_schedules(self):
        # type: () -> List[SaleProductManage]
        """ 可
        """
        today = datetime.date.today()
        base_qs = self.get_queryset().filter(Q(sale_time__gte=today)|Q(offshelf_time__gt=today))
        return base_qs.filter(schedule_type=self.model.SP_TOPIC)
