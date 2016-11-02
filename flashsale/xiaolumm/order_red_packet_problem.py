# coding=utf-8
from flashsale.clickrebeta.models import StatisticsShopping
from .models import OrderRedPacket, CarryLog, XiaoluMama
import datetime

TIME_FROM = datetime.datetime(2015, 7, 6, 0, 0, 0)
TIME_TO = datetime.datetime(2015, 7, 10, 23, 59, 59)


def order_Red_Packet():
    today = datetime.date.today()
    level_2_mamas = XiaoluMama.objects.filter(agencylevel=2, charge_status=XiaoluMama.CHARGED)
    mama_id_list_first = []
    mama_id_list_ten = []
    for mama in level_2_mamas:
        # 7-6号 到 7-9号 之间 该代理（agencylecel = 2） 在  (StatisticsShopping 统计购买列表中的记录)
        shops = StatisticsShopping.objects.filter(linkid=mama.id, shoptime__gt=TIME_FROM, shoptime__lt=TIME_TO).exclude(
            status=StatisticsShopping.REFUNDED)

        order_pac_get, state = OrderRedPacket.objects.get_or_create(xlmm=mama.id)

        carry_logs = CarryLog.objects.filter(xlmm=mama.id, log_type=CarryLog.ORDER_RED_PAC)  # 该妈妈的订单红包状态记录

        # 如果大于等于一单 并且有订单红包记录
        if shops.count() >= 1 and carry_logs.count() == 0 and shops.count() < 10:
            # 并且没有发放红包的 OrderRedPacket 中没有首单红包的记录
            # 并且CarryLog 中没有该代理的订单红包记录的
            if order_pac_get.first_red is False:
                order_pac_get.first_red = True
                order_pac_get.save()
                # 修改订单红包状态
                # 新建CarryLog（PENDING）记录
                order_red_carry_log = CarryLog(xlmm=mama.id, value=880, buyer_nick=mama.weikefu,
                                               log_type=CarryLog.ORDER_RED_PAC,
                                               carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING,
                                               carry_date=today)
                order_red_carry_log.save()
                mam_dic = {'first': mama.id}
                mama_id_list_first.append(mam_dic)  # 添加到列表 运行的时候查看下 有多少妈妈有订单红包问题

        # 如果大于等于十单
        if shops.count() >= 10:
            if carry_logs.count() == 0:  # 没有发放过红包
                if order_pac_get.ten_order_red is False:
                    # 并且没有发放十单红包的 OrderRedPacket
                    order_pac_get.ten_order_red = True
                    order_pac_get.save()
                    # 修改订单红包状态
                    # 新建CarryLog（PENDING）记录
                    order_red_carry_log = CarryLog(xlmm=mama.id, value=1880, buyer_nick=mama.weikefu,
                                                   log_type=CarryLog.ORDER_RED_PAC,
                                                   carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING,
                                                   carry_date=today)
                    order_red_carry_log.save()
                    mama_id_list_ten.append({'ten': mama.id})
            else:
                for carry in carry_logs:
                    if carry.value != 1880:  # 有首单红包没有十单红包 # 并且CarryLog 中没有该代理的订单红包记录的
                        if order_pac_get.ten_order_red is False:
                            # 并且没有发放十单红包的 OrderRedPacket
                            order_pac_get.ten_order_red = True
                            order_pac_get.save()
                            # 修改订单红包状态
                            # 新建CarryLog（PENDING）记录
                            order_red_carry_log = CarryLog(xlmm=mama.id, value=1880, buyer_nick=mama.weikefu,
                                                           log_type=CarryLog.ORDER_RED_PAC,
                                                           carry_type=CarryLog.CARRY_IN, status=CarryLog.PENDING,
                                                           carry_date=today)
                            order_red_carry_log.save()
                            mama_id_list_ten.append({'ten': mama.id})

