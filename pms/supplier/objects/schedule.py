from django.db import models
from core.managers import BaseManager


class ScheduleDetailManager(BaseManager):

    def set_material_complete_by_saleproduct(self, sale_product):
        details = self.filter(sale_product_id=sale_product.id)
        for schedule_detail in details:
            schedule_detail.set_material_status_complete()
            schedule_detail.save()

    def set_design_complete_by_saleproduct(self, sale_product):
        details = self.filter(sale_product_id=sale_product.id)
        for schedule_detail in details:
            schedule_detail.set_design_complete()
            schedule_detail.save()