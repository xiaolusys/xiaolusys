# coding=utf-8
from core.managers import BaseManager


class SaleSupplierManager(BaseManager):
    def charge(self, supplier, user, *args, **kwargs):

        from .. import SupplierCharge

        try:
            SupplierCharge.objects.get(
                supplier_id=supplier.id,
                status=SupplierCharge.EFFECT)
        except SupplierCharge.DoesNotExist:
            scharge, state = SupplierCharge.objects.get_or_create(
                supplier_id=supplier.id,
                employee=user)
            scharge.status = SupplierCharge.EFFECT
            scharge.save()
        else:
            return False

        supplier.status = self.model.CHARGED
        supplier.save()
        return True

    def uncharge(self, supplier, *args, **kwargs):

        from .. import SupplierCharge

        try:
            scharge = SupplierCharge.objects.get(
                supplier_id=supplier.id,
                status=SupplierCharge.EFFECT)
        except SupplierCharge.DoesNotExist:
            return False
        else:
            scharge.status = SupplierCharge.INVALID
            scharge.save()

        supplier.status = self.model.UNCHARGE
        supplier.save()
        return True