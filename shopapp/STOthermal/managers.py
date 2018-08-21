# -*- coding: utf-8 -*-

from django.db import models

class STOThermalQuerySet(models.QuerySet):
    def nihao(self):
        print 'nihao'

    def create_thermal(self, waybill_code, operation_user_id):
        thermal = self.create(waybill_code=waybill_code,operation_user_id=operation_user_id)
        return thermal

    def delete_thermal(self, waybill_code):
        self.filter(waybill_code=waybill_code).delete()