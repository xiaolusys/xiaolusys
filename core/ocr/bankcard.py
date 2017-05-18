# coding: utf8
from __future__ import absolute_import, unicode_literals

def verify(acc_no, acc_name):
    """
    :param acc_no: 卡号
    :param acc_name:　持有人姓名
    :return: 是否有效

    luhn algorithm:
    算法链接: http://www.yinhangkahao.com/bank_luhm.html
    """
    if len(acc_no) < 15:
        return False

    digits = [int(x) for x in reversed(str(acc_no))]
    check_sum = sum(digits[::2]) + sum((dig // 10 + dig % 10) for dig in [2 * el for el in digits[1::2]])
    return check_sum % 10 == 0