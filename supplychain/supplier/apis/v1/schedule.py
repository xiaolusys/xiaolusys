# coding=utf-8
__ALL__ = [
    'get_future_schedules',
    'get_future_topic_schedules',
    'get_schedule_products_by_schedule_id',
]

from ...models.schedule import SaleProductManage, SaleProductManageDetail


def get_schedule_by_id(id):
    # type: (int) -> SaleProductManage
    return SaleProductManage.objects.get(id=id)


def get_future_schedules():
    # type: () -> List[SaleProductManage]
    """未来排期
    """
    return SaleProductManage.objects.future_schedules()


def get_future_topic_schedules():
    # type: () -> List[SaleProductManage]
    """未来专题排期
    """
    return SaleProductManage.objects.future_topic_schedules()


def get_schedule_products_by_schedule_id(schedule_id):
    return SaleProductManageDetail.objects.filter(schedule_manage__id=schedule_id)