# # coding: utf-8
#
# import copy
# import json
# from django.test import TestCase
#
# from flashsale.dinghuo.models import InBound, InBoundDetail, OrderList, OrderDetail
# from flashsale.dinghuo.views import InBoundViewSet
# from shopback.items.models import ProductSku
#
#
# class InBoundTestCase(TestCase):
#     fixtures = [
#         'test.inbound.user.json', 'test.inbound.supplier.json',
#         'test.inbound.productcategory.json', 'test.inbound.product.json',
#         'test.inbound.productsku.json', 'test.inbound.orderlist.json',
#         'test.inbound.orderdetail.json'
#     ]
#
#     def setUp(self):
#         self.username = 'enjun.wang'
#         self.password = 'enjun.wang2015'
#         self.client.login(username=self.username, password=self.password)
#
#     def _create(self, data):
#         r = self.client.post('/sale/dinghuo/inbound/create_inbound',
#                              {'inbound_skus': json.dumps(data),
#                               'memo': '',
#                               'supplier_id': 28712},
#                              ACCPET='application/json')
#         self.assertEqual(r.status_code, 200)
#         result = json.loads(r.content)
#         self.assertIn('inbound', result)
#         self.assertGreater(result['inbound']['id'], 0)
#         return result
#
#     def _allocate(self, data):
#         result = self._create(data)
#
#         inbound_id = result['inbound']['id']
#         allocate_dict = result['allocate_dict']
#         details_dict = result['inbound']['details']
#
#         orderdetails_dict = {}
#         skus_dict = {}
#         allocate_data = []
#         for orderdetail in OrderDetail.objects.filter(
#                 id__in=allocate_dict.keys()):
#             self.assertIn(orderdetail.chichu_id, details_dict)
#             allocate_data.append({
#                 'sku_id': int(orderdetail.chichu_id),
#                 'inbounddetail_id': details_dict[orderdetail.chichu_id]['id'],
#                 'orderdetail_id': orderdetail.id,
#                 'arrival_quantity': allocate_dict[str(orderdetail.id)]
#             })
#
#             sku = ProductSku.objects.get(id=orderdetail.chichu_id)
#             orderdetails_dict[orderdetail.id] = orderdetail.arrival_quantity
#             skus_dict[sku.id] = sku.quantity
#
#         r = self.client.post('/sale/dinghuo/inbound/allocate',
#                              {'data': json.dumps(allocate_data),
#                               'inbound_id': inbound_id},
#                              ACCEPT='application/json')
#         self.assertEqual(r.status_code, 200)
#         result = json.loads(r.content)
#         self.assertIn('inbound', result)
#         self.assertIn('id', result['inbound'])
#         self.assertIn('records', result)
#
#         for sku_id, inbound_item in data.iteritems():
#             sku = ProductSku.objects.get(id=sku_id)
#             self.assertEqual(
#                 sku.quantity,
#                 skus_dict[sku_id] + inbound_item['arrival_quantity'])
#
#         for orderdetail_id, n in orderdetails_dict.iteritems():
#             orderdetail = OrderDetail.objects.get(id=orderdetail_id)
#             self.assertEqual(orderdetail.arrival_quantity,
#                              n + allocate_dict[str(orderdetail.id)])
#
#         return result
#
#     def _reallocate(self, data):
#         result = self._allocate(data)
#         orderdetails_dict = {}
#         skus_dict = {}
#         inferior_quantities_dict = {}
#         records = result['records']
#
#         for sku_id, inbound_item in data.iteritems():
#             inferior_quantities_dict[sku_id] = inbound_item['inferior_quantity']
#
#         for record in sorted(records,
#                              key=lambda x: x['orderdetail_id'],
#                              reverse=True):
#             sku_id = record['sku_id']
#             orderdetail_id = record['orderdetail_id']
#
#             sku = ProductSku.objects.get(id=sku_id)
#             orderdetail = OrderDetail.objects.get(id=orderdetail_id)
#
#             skus_dict[sku.id] = sku.quantity
#             inferior_quantity = data[sku_id]['inferior_quantity']
#
#             if inferior_quantity > 0:
#                 inferior_quantity = min(record['arrival_quantity'],
#                                         inferior_quantity)
#                 record['arrival_quantity'] -= inferior_quantity
#                 record['inferior_quantity'] = inferior_quantity
#                 data[sku_id]['inferior_quantity'] -= inferior_quantity
#                 orderdetails_dict[orderdetail_id] = {
#                     'arrival_quantity':
#                     orderdetail.arrival_quantity - inferior_quantity,
#                     'inferior_quantity':
#                     orderdetail.inferior_quantity + inferior_quantity
#                 }
#             else:
#                 record['inferior_quantity'] = 0
#                 orderdetails_dict[orderdetail_id] = {
#                     'arrival_quantity': orderdetail.arrival_quantity,
#                     'inferior_quantity': orderdetail.inferior_quantity
#                 }
#
#         r = self.client.post('/sale/dinghuo/inbound/reallocate',
#                              {'data': json.dumps(records),
#                               'inbound_id': result['inbound']['id']},
#                              ACCEPT='application/json')
#         self.assertEqual(r.status_code, 200)
#         result = json.loads(r.content)
#
#         for sku_id, inbound_item in data.iteritems():
#             sku = ProductSku.objects.get(id=sku_id)
#             self.assertEqual(sku.quantity, skus_dict[sku_id] -
#                              inferior_quantities_dict[sku.id])
#
#         for orderdetail_id, orderdetail_dict in orderdetails_dict.iteritems():
#             orderdetail = OrderDetail.objects.get(id=orderdetail_id)
#             self.assertEqual(orderdetail.arrival_quantity,
#                              orderdetail_dict['arrival_quantity'])
#             self.assertEqual(orderdetail.inferior_quantity,
#                              orderdetail_dict['inferior_quantity'])
#
#     def test_create(self):
#         data = {
#             '162264': {
#                 'product_id': 40243,
#                 'sku_id': 162264,
#                 'arrival_quantity': 6
#             }
#         }
#         self._create(data)
#
#     def test_allocate(self):
#         inbound_data = {
#             162264: {
#                 'product_id': 40243,
#                 'sku_id': 162264,
#                 'arrival_quantity': 8
#             },
#             162258: {
#                 'product_id': 40242,
#                 'sku_id': 162258,
#                 'arrival_quantity': 6
#             }
#         }
#
#         r = self.client.post('/sale/dinghuo/inbound/create_inbound',
#                              {'inbound_skus': json.dumps(inbound_data),
#                               'memo': '',
#                               'supplier_id': 28712},
#                              ACCEPT='application/json')
#         self.assertEqual(r.status_code, 200)
#         result = json.loads(r.content)
#
#         self.assertIn('allocate_dict', result)
#         self.assertIn('inbound', result)
#         self.assertIn('details', result['inbound'])
#
#     def test_rellocate(self):
#         inbound_data = {
#             162259: {
#                 'arrival_quantity': 14,
#                 'inferior_quantity': 3,
#             },
#             162290: {
#                 'arrival_quantity': 1,
#                 'inferior_quantity': 1
#             },
#             162397: {
#                 'arrival_quantity': 2,
#                 'inferior_quantity': 2
#             }
#         }
#         self._reallocate(inbound_data)
#
#     def test_optimized_allocate(self):
#         inbound_skus_dict = {
#             162255: {
#                 "arrival_quantity": 1
#             },
#             162258: {
#                 "arrival_quantity": 5
#             },
#             162259: {
#                 "arrival_quantity": 10
#             },
#             162262: {
#                 "arrival_quantity": 1
#             },
#             162264: {
#                 "arrival_quantity": 1
#             },
#             162305: {
#                 "arrival_quantity": 1
#             },
#             162345: {
#                 "arrival_quantity": 1
#             },
#             162397: {
#                 "arrival_quantity": 1
#             },
#             162407: {
#                 "arrival_quantity": 1
#             }
#         }
#
#         allocate_dict = InBoundViewSet._find_optimized_allocate_dict(inbound_skus_dict, [16713, 16748, 16831], 16713, '')
#         for orderdetail in OrderDetail.objects.filter(orderlist_id=16831):
#             self.assertIn(orderdetail.id, allocate_dict)
#             self.assertEqual(max(orderdetail.buy_quantity - orderdetail.arrival_quantity, 0), allocate_dict[orderdetail.id])
