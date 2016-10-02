# -*- encoding:utf-8 -*-

import random


def get_ordercarry_description(via_app=False, second_level=False):
    second_level_desc = [
        "嘿嘿，下属妈妈的佣金又到啦～",
        "下属佣金，休息日子也能拿哦！",
        "下属佣金，一直不忘您的推荐！",
        "下属佣金，细钱长流～",
        "下属佣金，在不知不觉中积累。",
        "下属佣金，感谢老大推荐我！"
    ]
    via_app_desc = [
        "APP粉丝佣金，来得更直接！",
        "APP粉丝佣金，直接找到您！",
        "APP粉丝佣金，粉丝多赚钱快！",
        "APP粉丝佣金，跟定你啦~",
        "APP粉丝佣金，真的粉丝经济。",
        "APP粉丝佣金，您的粉丝号召力。",
        "APP粉丝佣金，粉丝就是财富。",
        "APP粉丝佣金，让粉丝更多吧～",
        "APP粉丝佣金，抓紧加粉丝！",
        "APP粉丝佣金，努力加粉丝哦！"
    ]
    other_desc = [
        "坐收佣金，好羡慕啊～",
        "躺着也能赚钱呢～",
        "马上就变白富美啦～",
        "亲，佣金又多些了呢～",
        "感谢佣金涌来的日子。",
        "订单佣金，对努力的肯定",
        "订单佣金，只需APP分享一下",
        "订单佣金，来得如此简单",
        "佣金不断向您涌来。。。",
        "一大笔佣金正在赶来。。。",
        "APP一键分享，佣金自来。",
        "APP分享拿佣金，更方便啦～",
        "APP分享拿佣金，更高效啦～"
    ]

    if via_app:
        return random.choice(via_app_desc)
    if second_level:
        return random.choice(second_level_desc)
    return random.choice(other_desc)


def get_awardcarry_description(carry_type):
    referal_desc = [
        "表现优异，奖金都拿到啦～",
        "亲，您奖金更多些了呢～",
        "奖金就要大幅上涨啦，加油！",
        "向金牌妈妈努力吧！",
        "奖金到手，金牌妈妈不远啦！",
        "继续推荐，让奖金潮水般涌来!",
        "对不起，又有奖金砸到您啦！",
        "每天收奖金，是最美好的事。",
        "记住，推荐15个就金牌妈妈哦!",
        "向金牌妈妈努力进发吧!",
        "每天拿奖金的记忆，要继续！",
        "奖金和努力成正比，谢谢您！"
    ]
    group_desc = [
        "哇塞，又有队员加入啦!",
        "哇塞，奖金拿得好爽呀～",
        "新队员加入，团队又壮大咯～",
        "报告团长，新成员奖金已入账！",
        "亲，您的团队让人妒忌～",
        "团长，每天奖金收不停。",
        "团队奖金赞，让妈妈们加油哦～",
        "奖金接住！要带领最强的团队！",
        "加油！团队士气正旺！",
        "团队在成长，奖金在增多。。。",
        "我的团队，奖金归我。",
        "有团队就有一切，有奖金～"
    ]
    lesson_desc = [
        "您的课太精彩啦～",
        "加油，就快成金牌讲师啦～",
        "小鹿大学，让推广更专业～",
        "最专业的课都在小鹿大学!",
        "三人行，必有我师!",
        "小鹿大学，敢讲就能成讲师!",
        "亲，你比马云更会讲呢!",
        "小鹿大学，让收益来得更轻松!"
    ]

    if carry_type == 1:
        return random.choice(referal_desc)
    if carry_type == 2:
        return random.choice(group_desc)
    return random.choice(lesson_desc)


def get_clickcarry_description():
    desc = [
        "亲，你每天都有返现拿哦～",
        "订单越多，返现越多哦！",
        "每天都有返现，好日子么么哒~",
        "分享10秒，返现已到！",
        "APP分享便捷，返现自动涌来。",
        "这辈子每天这么返，不要停！",
        "每天返现，只在小鹿妈妈。",
        "追忆似水年华的返现日子。。。",
        "不放过任何一天的返现。",
        "每天第一件事：分享返现！",
        "返现的大日子，终于等到您！"
    ]

    return random.choice(desc)


def gen_activevalue_description(value_type):
    desc = [
        "",
        "点击活跃值 +%d",
        "订单活跃值 +%d",
        "推荐小鹿妈妈活跃值 +%d",
        "粉丝活跃值 +%d",
    ]
    from flashsale.xiaolumm.models.models_fortune import ActiveValue
    value_num = ActiveValue.VALUE_MAP[str(value_type)]

    return desc[value_type] % value_num


def get_awardcarry_courage_remarks(carry_type):
    """
    (1, u'直荐奖励'),(2, u'团队奖励'),(3, u'授课奖金'),(4, u'新手任务'),(5, u'首单奖励'),(6, u'推荐新手任务'),(7, u'一元邀请'))
    """
    desc = {
        "1": u"恭喜又多了一位才华横溢的妈妈队员，建议学习发特卖教程，点击就赚0.1元！点击［详情］查看。",
        "2": u"团队又壮大啦，注意要多辅导新人哦！",
        "3": u"妈妈上讲台，朋友和孩子以后也会勇敢上讲台！",
        "4": u"恭喜新手任务完成，您已经可以辅导其他妈妈啦！",
        "5": u"首单奖励已到，完成其他任务还有奖励哦！",
        "6": u"加油！您的团队更专业啦！记得检查新手妈妈完成任务哦！",
        "7": u"加油！多推荐几个，更多奖金！新手任务完成还有额外奖励哦！",
    }
    key = str(carry_type)
    return desc.get(key, '')
