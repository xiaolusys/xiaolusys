# coding=utf-8
from shopback.outware import constants
from shopback.trades.models import PackageOrder, PackageSkuItem
from shopback.refunds.models import Refund, RefundProduct
from shopback.logistics.models import LogisticsCompany
from shopback.items.models import ProductSku

class ReturnStoreRunner(object):
    def __init__(self, outware_packages):
        self.outware_packages = outware_packages

    def execute(self):
        for outware_package in self.outware_packages:
            package_order = PackageOrder.objects.get(pid=outware_package.package_order_code)
            new_package = package_order.divide(outware_package.get_sku_dict())
            if new_package:
                package_order = new_package
            logistics_company = LogisticsCompany.get_by_fengchao_code(outware_package.carrier_code)
            package_order.fininsh_third_send(outware_package.logistics_no, logistics_company)
        return self.outware_packages


class SaleOutRunner(object):
    """
        出货执行
    """
    def __init__(self, outware_packages):
        self.outware_packages = outware_packages

    def execute(self):
        for outware_package in self.outware_packages:
            package_order = PackageOrder.objects.get(pid=outware_package.package_order_code)
            sku_ori_dict  = outware_package.get_sku_dict()
            sku_dict = {str(ProductSku.objects.get(outer_id=key).id): sku_ori_dict[key] for key in sku_ori_dict}
            new_package = package_order.divide(sku_dict)
            if new_package:
                package_order = new_package
            logistics_company = LogisticsCompany.get_by_fengchao_code(outware_package.carrier_code)
            package_order.finish_third_package(outware_package.logistics_no, logistics_company)
        return self.outware_packages


def get_runner(code):
    s = {
        constants.ORDER_RETURN['code']: ReturnStoreRunner,
        constants.ORDER_SALE['code']: SaleOutRunner,
    }
    return s[code]