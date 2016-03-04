__author__ = 'yann'
from supplychain.supplier.models import SupplierCharge, SaleProduct
from django.contrib.auth.models import User as DjangoUser
from core.options import log_action, ADDITION, CHANGE
NEED_CHANGE = """
{'employee_id': 80L, 'employee__username': u'aileen.zhang'}!
{'employee_id': 99L, 'employee__username': u'bing.luo'}!
{'employee_id': 135L, 'employee__username': u'cgroupa'}!
{'employee_id': 137L, 'employee__username': u'cgroupc'}!
{'employee_id': 92L, 'employee__username': u'chao.he'}!
{'employee_id': 159L, 'employee__username': u'chuanyun.huang'}!
{'employee_id': 74L, 'employee__username': u'danni.zhu'}!
{'employee_id': 71L, 'employee__username': u'fangfang.yang'}!
{'employee_id': 81L, 'employee__username': u'fangxia.xiong'}!
{'employee_id': 25L, 'employee__username': u'fay.yan'}!
{'employee_id': 85L, 'employee__username': u'fengtao.nie'}!
{'employee_id': 142L, 'employee__username': u'guangping.yang'}!
{'employee_id': 103L, 'employee__username': u'haoming.yao'}!
{'employee_id': 122L, 'employee__username': u'heli.li'}!
{'employee_id': 32L, 'employee__username': u'jessica.dong'}!
{'employee_id': 66L, 'employee__username': u'jianguo.xiao'}!
{'employee_id': 105L, 'employee__username': u'jieni.qin'}!
{'employee_id': 116L, 'employee__username': u'joan.tong'}!
{'employee_id': 64L, 'employee__username': u'july.yan'}!
{'employee_id': 95L, 'employee__username': u'kai.qiu'}!
{'employee_id': 63L, 'employee__username': u'laura.zhang'}!
{'employee_id': 164L, 'employee__username': u'lei.fan'}!
{'employee_id': 123L, 'employee__username': u'lin.zhu'}!
{'employee_id': 108L, 'employee__username': u'linyun.cao'}!
{'employee_id': 114L, 'employee__username': u'liqing.wang'}!
{'employee_id': 21L, 'employee__username': u'lisa.xie'}!
{'employee_id': 117L, 'employee__username': u'lu.tian'}!
{'employee_id': 150L, 'employee__username': u'mei.liu'}!
{'employee_id': 73L, 'employee__username': u'na.zhao'}!
{'employee_id': 82L, 'employee__username': u'peipei.zhang'}!
{'employee_id': 132L, 'employee__username': u'pinting.cao'}!
{'employee_id': 70L, 'employee__username': u'pucci.li'}!
{'employee_id': 87L, 'employee__username': u'qian.yang'}!
{'employee_id': 15L, 'employee__username': u'qiaoying.she'}!
{'employee_id': 160L, 'employee__username': u'sangsang.gan'}!
{'employee_id': 69L, 'employee__username': u'selina.zhang'}!
{'employee_id': 148L, 'employee__username': u'shanshan.zhou'}!
{'employee_id': 30L, 'employee__username': u'shao.shao'}!
{'employee_id': 158L, 'employee__username': u'shaoqin.lai'}!
{'employee_id': 110L, 'employee__username': u'shuang.du'}!
{'employee_id': 121L, 'employee__username': u'tianyu.liu'}!
{'employee_id': 65L, 'employee__username': u'wei.chen'}!
{'employee_id': 68L, 'employee__username': u'wei.shi'}!
{'employee_id': 100L, 'employee__username': u'xiaoqi.ma'}!
{'employee_id': 115L, 'employee__username': u'xiaoting.wang'}!
{'employee_id': 1L, 'employee__username': u'xiuqing.mei'}!
{'employee_id': 162L, 'employee__username': u'xueqin.xie'}!
{'employee_id': 67L, 'employee__username': u'yang.chen'}!
{'employee_id': 96L, 'employee__username': u'yingcheng.li'}!
{'employee_id': 161L, 'employee__username': u'yujun.gu'}!
{'employee_id': 98L, 'employee__username': u'yuming.jiang'}!
{'employee_id': 6L, 'employee__username': u'zifei.zhong'}!
{'employee_id': 133L, 'employee__username': u'zijing.fu'}
"""


PRODUCT_NEED_CHANGE = """
{'contactor_id': 63L, 'contactor__username': u'laura.zhang'}!
{'contactor_id': 64L, 'contactor__username': u'july.yan'}!
{'contactor_id': 65L, 'contactor__username': u'wei.chen'}!
{'contactor_id': 66L, 'contactor__username': u'jianguo.xiao'}!
{'contactor_id': 67L, 'contactor__username': u'yang.chen'}!
{'contactor_id': 68L, 'contactor__username': u'wei.shi'}!
{'contactor_id': 69L, 'contactor__username': u'selina.zhang'}!
{'contactor_id': 70L, 'contactor__username': u'pucci.li'}!
{'contactor_id': 71L, 'contactor__username': u'fangfang.yang'}!
{'contactor_id': 73L, 'contactor__username': u'na.zhao'}!
{'contactor_id': 74L, 'contactor__username': u'danni.zhu'}!
{'contactor_id': 80L, 'contactor__username': u'aileen.zhang'}!
{'contactor_id': 81L, 'contactor__username': u'fangxia.xiong'}!
{'contactor_id': 82L, 'contactor__username': u'peipei.zhang'}!
{'contactor_id': 85L, 'contactor__username': u'fengtao.nie'}!
{'contactor_id': 87L, 'contactor__username': u'qian.yang'}!
{'contactor_id': 92L, 'contactor__username': u'chao.he'}!
{'contactor_id': 95L, 'contactor__username': u'kai.qiu'}!
{'contactor_id': 96L, 'contactor__username': u'yingcheng.li'}!
{'contactor_id': 98L, 'contactor__username': u'yuming.jiang'}!
{'contactor_id': 99L, 'contactor__username': u'bing.luo'}!
{'contactor_id': 100L, 'contactor__username': u'xiaoqi.ma'}!
{'contactor_id': 103L, 'contactor__username': u'haoming.yao'}!
{'contactor_id': 105L, 'contactor__username': u'jieni.qin'}!
{'contactor_id': 108L, 'contactor__username': u'linyun.cao'}!
{'contactor_id': 109L, 'contactor__username': u'jie.gan'}!
{'contactor_id': 110L, 'contactor__username': u'shuang.du'}!
{'contactor_id': 111L, 'contactor__username': u'mengqi.zhu'}!
{'contactor_id': 112L, 'contactor__username': u'zhongfa.zeng'}!
{'contactor_id': 114L, 'contactor__username': u'liqing.wang'}!
{'contactor_id': 115L, 'contactor__username': u'xiaoting.wang'}!
{'contactor_id': 116L, 'contactor__username': u'joan.tong'}!
{'contactor_id': 117L, 'contactor__username': u'lu.tian'}!
{'contactor_id': 121L, 'contactor__username': u'tianyu.liu'}!
{'contactor_id': 122L, 'contactor__username': u'heli.li'}!
{'contactor_id': 123L, 'contactor__username': u'lin.zhu'}!
{'contactor_id': 132L, 'contactor__username': u'pinting.cao'}!
{'contactor_id': 133L, 'contactor__username': u'zijing.fu'}!
{'contactor_id': 135L, 'contactor__username': u'cgroupa'}!
{'contactor_id': 137L, 'contactor__username': u'cgroupc'}!
{'contactor_id': 139L, 'contactor__username': u'yan.huang'}!
{'contactor_id': 142L, 'contactor__username': u'guangping.yang'}!
{'contactor_id': 148L, 'contactor__username': u'shanshan.zhou'}!
{'contactor_id': 150L, 'contactor__username': u'mei.liu'}!
{'contactor_id': 159L, 'contactor__username': u'chuanyun.huang'}!
{'contactor_id': 160L, 'contactor__username': u'sangsang.gan'}!
{'contactor_id': 161L, 'contactor__username': u'yujun.gu'}!
{'contactor_id': 162L, 'contactor__username': u'xueqin.xie'}!
{'contactor_id': 164L, 'contactor__username': u'lei.fan'}
"""

DJUSER, STATE = DjangoUser.objects.get_or_create(username='systemoa', is_active=True)

def change(o_id, n_id):
    a = SupplierCharge.objects.filter(employee_id=o_id)
    for b in a:
        b.employee_id = n_id
        b.save()
        log_action(DJUSER.id, b, CHANGE, u'system_change_user')


def change_product(o_id, n_id):
    aa = SaleProduct.objects.filter(contactor_id=o_id)
    for bb in aa:
        bb.contactor_id = n_id
        bb.save()
        log_action(DJUSER.id, bb, CHANGE, u'system_change_user')


def p_change():
    all_list = NEED_CHANGE.split("!")
    for one in all_list:
        one_user = eval(one)
        system_user = DjangoUser.objects.filter(username=one_user["employee__username"])
        if system_user.count() > 0:
            change(int(one_user["employee_id"]), int(system_user[0].id))
            print one_user["employee__username"], "---OK"
        else:
            print one_user["employee__username"], "---fail"


def p_change_2():
    all_list = PRODUCT_NEED_CHANGE.split("!")
    for one in all_list:
        one_user = eval(one)
        system_user = DjangoUser.objects.filter(username=one_user["contactor__username"])
        if system_user.count() > 0:
            change_product(int(one_user["contactor_id"]), int(system_user[0].id))
            print one_user["contactor__username"], "---OK"
        else:
            print one_user["contactor__username"], "---fail"
