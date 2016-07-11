# coding=utf-8
import datetime
from celery.task import task
from supplychain.supplier.models import SaleProductManage, SaleProductManageDetail
from core.options import get_systemoa_user, log_action
from django.contrib.admin.models import CHANGE
from shopback.items.models import Product
import logging

logger = logging.getLogger(__name__)


@task(max_retries=3, default_retry_delay=5)
def task_sync_shelf_time_from_manager():
    """
    同步 排期明细中的产品　的上下架时间到　库存商品列表中的上下架时间
    方法：　未来的排期明细中　与当前时期最近的　明细　的上下架时间　更新　库存商品上下架时间
    """
    now = datetime.datetime.now()
    next_time = now + datetime.timedelta(days=2)  # 同步两天内　　排期管理记录
    managers = SaleProductManage.objects.filter(lock_status=True,
                                                upshelf_time__gte=now,  # 上架时间大于现在时间（未来）
                                                upshelf_time__lte=next_time,  # 上架时间小于两天后
                                                upshelf_time__isnull=False,
                                                offshelf_time__isnull=False).order_by('upshelf_time')
    # 按照时间排序（方便后面　取　最近的排期时间）

    for manager in managers:
        logger.warn(u'task_sync_shelf_time_from_manager manage id is %s , up %s - off %s' % (
            manager.id, manager.upshelf_time, manager.offshelf_time))

        details = manager.manage_schedule.filter(material_status=SaleProductManageDetail.COMPLETE,  # 资料全部完成
                                                 today_use_status=SaleProductManageDetail.NORMAL,  # 正常使用状态
                                                 design_take_over=SaleProductManageDetail.TAKEOVER)  # 接管过的

        detail_sale_products = details.values('sale_product_id')
        systemoa = get_systemoa_user()

        def update_pro_shelf_time(upshelf_time, offshelf_time):
            def _wrapper(p):
                print upshelf_time, offshelf_time
                state = p.update_shelf_time(upshelf_time, offshelf_time)
                if state:
                    log_action(systemoa, p, CHANGE, u'系统自动同步排期时间')

            return _wrapper

        try:
            for sale_product in detail_sale_products:
                pros = Product.items_by_sale_product_id(sale_product['sale_product_id'])
                map(update_pro_shelf_time(manager.upshelf_time, manager.offshelf_time), pros)  # 更新上下架时间
        except Exception as exc:
            raise task_sync_shelf_time_from_manager.retry(countdown=60 * 10, exc=exc)

