import datetime
# coding=utf-8

def gen_ordercarry_unikey(carry_type, order_id):
    # For each type ordercarry, a single order only generate once such carry.
    if carry_type == 1 or carry_type == 2:
        carry_type = 1
    return '-'.join(['order', str(carry_type), order_id])


def gen_awardcarry_unikey(from_mama_id, to_mama_id):
    return '-'.join(['award', str(from_mama_id), str(to_mama_id)])


def gen_clickcarry_unikey(mama_id, date):
    return '-'.join(['click', str(mama_id), str(date)])


def gen_activevalue_unikey(value_type, mama_id, date, order_id, contributor_id):
    if value_type == 1:  # click
        return '-'.join(['active', str(mama_id), str(value_type), str(date)])
    if value_type == 2:  # order
        return '-'.join(['active', str(mama_id), str(value_type), str(date), str(order_id)])
    if value_type == 3:  # referal
        return '-'.join(['active', str(mama_id), str(value_type), str(contributor_id)])
    if value_type == 4:  # fans
        return '-'.join(['active', str(mama_id), str(value_type), str(contributor_id)])
    return ""


def gen_uniquevisitor_unikey(openid, date_field):
    return "-".join([openid, str(date_field)])


def gen_dailystats_unikey(mama_id, date_field):
    return "-".join([str(mama_id), str(date_field)])


def gen_lessonattendrecord_unikey(lesson_id, unionid):
    return '-'.join([str(lesson_id), unionid])


def gen_topicattendrecord_unikey(topic_id, unionid):
    """
    uni_key = topic_id + unionid + year + week
    """
    today = datetime.date.today().isocalendar()

    year = today[0]
    week = today[1]

    return '-'.join([str(topic_id), str(unionid), str(year), str(week)])
    

