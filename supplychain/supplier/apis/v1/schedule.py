# coding=utf-8
from ...models.schedule import SaleProductManage, SaleProductManageDetail


def get_future_schedules():
    # type: () -> List[SaleProductManage]
    """未来排期
    """
    return SaleProductManage.objects.future_schedules()


def get_schedule_products_by_schedule_id(schedule_id):
    return SaleProductManageDetail.objects.filter(schedule_manage__id=schedule_id)