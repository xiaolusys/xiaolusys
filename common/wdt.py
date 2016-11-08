# encoding=utf8
import urllib
import base64
from hashlib import md5
from datetime import datetime

import requests
import simplejson


class WangDianTong(object):

    # url = 'http://121.199.38.85/openapi/interface.php'
    # key = '12345'
    # interface_id = 'euhotest',
    # seller_id = 'dev5',

    url = 'http://api.wangdian.cn/stockapi/interface.php'
    key = '236993f5289a61dbc4fff617dd890bb9'
    interface_id = 'euho-ot'
    seller_id = 'euho'

    def sign(self, str):
        return urllib.quote(base64.b64encode(md5(str).hexdigest()))

    def _request(self, method, content):
        """
        params:
        - method => str
        - content => dict
        """
        content = simplejson.dumps(content)
        data = {
            'Method': method,
            'SellerID': self.seller_id,
            'InterfaceID': self.interface_id,
            'Sign': self.sign(content+self.key),
            'Content': content
        }
        resp = requests.post(self.url, data=data)
        return simplejson.loads(resp.content)

    def create_order(self):
        """
        创建订单
        """
        content = {
            'OutInFlag': 3,
            'IF_OrderCode': 'waibubianhao992398',  # 外部单据编号
            'WarehouseNO': '001',  # 优禾主仓库
            'Remark': '小鹿美美测试不用发货2',  # 备注
            'GoodsTotal': 1.90,  # 货款合计(销售出库时非空)
            'OrderPay': 1.90,  # 订单付款金额（含运费）
            'LogisticsPay': 0.0,  # 运费
            'ShopName': '优禾生活小鹿美美店',  # 订单所属店铺名称（出库时非空）
            'BuyerName': 'name',  # 收货人姓名
            'BuyerPostCode': '453000',  # 收货人邮编
            'BuyerTel': '15712341234',
            'BuyerProvince': '北京',
            'BuyerCity': '北京',
            'BuyerDistrict': '海淀区',
            'BuyerAdr': '知春路',
            'PayTime': '2016-10-29 00:00:01',
            'TradeTime': '2016-10-29 00:00:00',
            'ItemList': {
                'Item': [
                    {
                        'Sku_Code': '52064',
                        'Sku_Name': 'sku名称',
                        'Sku_Price': 1.9,
                        'Qty': 1,
                        'Total': 1.9,
                        # 'Discount': ''
                        'Item_Remark': 'sku备注',
                    }
                ]
            }

        }
        return self._request('NewOrder', content)

    def query_order(self, order_code):
        content = {
            'OrderCode': order_code
        }
        return self._request('QueryTradeByNO', content)

    def query_logistics(self, order_code):
        """
        查询订单是否发货，物流信息
        """
        json = self.query_order(order_code)
        trade_status = json['TradeStatus']  # 订单状态 over_trade已完成(表示已发货)
        snd_time = json['SndTime']  # 发货时间
        logistics_code = json['LogisticsCode']  # 物流公司编号
        logistics_name = json['LogisticsName']  # 物流公司名称
        post_id = json['PostID']  # 物流编号

        return {
            'trade_status': trade_status,
            'snd_time': snd_time,
            'logistics_code': logistics_code,
            'logistics_name': logistics_name,
            'post_id': post_id
        }

    def get_products(self, start_time=None, end_time=None, goods_no=None,
                     sku_code=None, page_no=1, page_size=40):
        """
        查询商品
        """
        content = {
            'StartTime': '2010-01-01 00:00:00',
            'EndTime': '2024-01-01 23:59:59',
            'PageNO': page_no,
            'PageSize': page_size
        }
        return self._request('QueryGoodsInfo', content)

    def receive_logistics(self, req):
        """
        Method=LogisticsReturn&SellerID=maijia&Sign=YUPljoslfoPO2KJL&Content=
        {
        “TradeList”:
        {
        “Trade”:
        [
        {
        “OrderCode”:”OR2013010101”,  # 外部系统订单编号
        “TradeNO”:”JY201301010001”,  # ERP内订单编号
        “ErpLogisticCode”: “SF”,
        “LogisticName”: “顺丰速运”,
        “PostID”: “3273832728”,
        “SndTime”:”2001-01-01 10:00:00”
        },
        {
        “OrderCode”:”OR2013010102”,
        “TradeNO”:”JY201301010002”,
        “ErpLogisticCode”: “EMS”,
        “LogisticName”: “EMS”,
        “PostID”: “3273832729”,
        “SndTime”:”2001-01-01 10:00:00”

        }
        ]
        }
        """
        print req.POST
        method = req.POST.get('Method', '')
        seller_id = req.POST.get('SellerID', '')
        sign = req.POST.get('Sign', '')
        content = req.POST.get('Content', '{}')

        content = simplejson.loads(content)
        trades = content.get('TradeList', {}).get('Trade', [])
        for trade in trades:
            print trade

        resp = {
            'ResultList': {
                'ResultCode': 0,  # 请求结果（0成功，非0失败）
                'ResultMsg': '',
                'Result': []
            }
        }
        for trade in trades:
            resp['ResultList']['Result'].append({
                'IF_OrderCode': trade['OrderCode'],  # 外部系统订单编号
                'ResultCode': '0',
                'ResultMsg': 'success'
            })
        print resp
        return resp


def main():
    wdt = WangDianTong()
    resp = wdt.create_order()
    resp = wdt.query_logistics('JY201611050016')
    # print simplejson.dumps(resp, indent=2)
    for k, v in resp.items():
        print k, v


if __name__ == '__main__':
    main()
