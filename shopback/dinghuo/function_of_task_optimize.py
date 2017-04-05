# *_* coding: utf-8 *_*
from django.db import connection


def get_sale_num(shelf_from, time_to, outer_id=None, outer_sku_id=None):
    """根据传入的时间范围和outer_id和sku_outer_id，返回销售数量"""
    order_sql = """
                    SELECT
                        outer_id, outer_sku_id, SUM(num) AS sale_num
                    FROM
                        shop_trades_mergeorder
                    WHERE
                        outer_id = '{0}'
                            AND outer_sku_id = '{1}'
                            AND refund_status = 'NO_REFUND'
                            AND sys_status = 'IN_EFFECT'
                            AND merge_trade_id IN (SELECT
                                id
                            FROM
                                shop_trades_mergetrade
                            WHERE
                                type NOT IN ('reissue' , 'exchange')
                                    AND status IN ('WAIT_SELLER_SEND_GOODS' , 'WAIT_BUYER_CONFIRM_GOODS',
                                    'TRADE_BUYER_SIGNED',
                                    'TRADE_FINISHED')
                                    AND sys_status NOT IN ('INVALID' , 'ON_THE_FLY')
                                    AND id NOT IN (SELECT
                                        id
                                    FROM
                                        shop_trades_mergetrade
                                    WHERE
                                        sys_status = 'FINISHED'
                                            AND is_express_print = FALSE))
                            AND gift_type != 4
                            AND (pay_time BETWEEN '{2}' AND '{3}')
                    GROUP BY outer_id , outer_sku_id
                """.format(outer_id, outer_sku_id, shelf_from, time_to)
    cursor = connection.cursor()
    cursor.execute(order_sql)
    order_raw = cursor.fetchall()
    return order_raw[0][2] if order_raw else 0


def get_dinghuo_num(dinghuo_begin, query_time, outer_id=None, sku_id=None):
    ding_huo_sql = """
        SELECT
            B.outer_id,
            B.chichu_id,
            SUM(IF(A.status = '草稿'
                    OR A.status = '审核',
                B.buy_quantity,
                0)) AS buy_quantity,
            SUM(IF(A.status = '7', B.buy_quantity, 0)) AS sample_quantity,
            SUM(IF(status = '5' OR status = '6'
                    OR status = '有问题'
                    OR status = '验货完成'
                    OR status = '已处理',
                B.arrival_quantity,
                0)) AS arrival_quantity,
            A.status
        FROM
            suplychain_flashsale_orderlist AS A,
            suplychain_flashsale_orderdetail AS B
        WHERE
            A.id = B.orderlist_id
                AND status NOT IN ('作废')
                AND A.created BETWEEN '{0}' AND '{1}'
                AND B.outer_id = '{2}'
                AND B.chichu_id = '{3}'
        GROUP BY B.outer_id , B.chichu_id;
    """.format(dinghuo_begin, query_time, outer_id, sku_id)
    cursor = connection.cursor()
    cursor.execute(ding_huo_sql)
    order_raw = cursor.fetchall()
    return order_raw[0][2] if order_raw else 0, order_raw[0][3] if order_raw else 0, order_raw[0][4] if order_raw else 0
