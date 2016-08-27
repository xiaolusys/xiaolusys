# encoding=utf8
class NewMamaTask(object):

    TASK_SUBSCRIBE_WEIXIN = u'subscribe_weixin'
    TASK_FIRST_CARRY = u'first_carry'
    TASK_FIRST_SHARE_COUPON = u'first_share_coupon'
    TASK_FIRST_FANS = u'first_fans'
    TASK_FIRST_MAMA_RECOMMEND = u'first_mama_recommend'
    TASK_FIRST_COMMISSION = u'first_commission'

    tasks = (
        (TASK_SUBSCRIBE_WEIXIN, u'关注微信公众号'),
        (TASK_FIRST_CARRY, u'获得第一笔点击收益'),
        (TASK_FIRST_FANS, u'发展第一个粉丝'),
        (TASK_FIRST_SHARE_COUPON, u'分享第一个红包'),
        (TASK_FIRST_COMMISSION, u'赚取第一笔佣金'),
        (TASK_FIRST_MAMA_RECOMMEND, u'发展第一个代理'),
    )

    @classmethod
    def get_push_msg(cls, task_name, params=None):
        items = {
            cls.TASK_SUBSCRIBE_WEIXIN: (
                u'关注公众号成功，您已获得５元奖励。\n',
                u'恭喜开通小鹿妈妈15天体验帐户！下载小鹿App，开启分享赚钱之旅！请加管理员微信，在管理员指导下，您会赚很多很多零花钱的哦！',
                'http://m.xiaolumeimei.com/sale/promotion/appdownload/',
            ),
            cls.TASK_FIRST_CARRY: (
                u'您的点击返现{money}元已经到账！挣钱太容易啦！\n',
                u'\n下一个任务：快去试试点击返现，点击就有钱到账！完成新手任务还有10元奖金等你呢！点击查看教程。',
                'http://mp.weixin.qq.com/s?__biz=MzA5MzQxMzU2Mg==&mid=2650808011&idx=2&sn=4015667e9c849cf17680a83d741c910b&scene=0',
            ),
            cls.TASK_FIRST_SHARE_COUPON: (
                u'恭喜分享红包成功\n',
                u'\n下一个任务：快去分享您的红包，自己点击领取吧！完成新手任务就有10元奖金等你哦！点击查看教程。',
                'http://mp.weixin.qq.com/s?__biz=MzIzODUyOTk1NA==&mid=2247483690&idx=2&sn=82c9cafd9820e2257090e5f4d38381f3&scene=0',
            ),
            cls.TASK_FIRST_FANS: (
                u'恭喜您获得了粉丝一枚！\n',
                u'\n下一个任务：快去获取您的第一位粉丝吧！完成新手任务就有10元奖金等你哦！点击查看教程。',
                'http://mp.weixin.qq.com/s?__biz=MzIzODUyOTk1NA==&mid=2247483690&idx=3&sn=bf031da7524edaf4b84bd5063c4c8cfd&scene=0',
            ),
            cls.TASK_FIRST_MAMA_RECOMMEND: (
                u'恭喜您推荐了一位1元体验妈妈！\n',
                u'\n下一个任务：快去推荐一位1元体验小鹿妈妈！推荐2名奖励5元！完成新手任务还有10元奖金等你哦！点击查看教程。',
                'http://mp.weixin.qq.com/s?__biz=MzA5MzQxMzU2Mg==&mid=2650808011&idx=5&sn=1a2ec2083149b4c0334d96c5eeff24b2',
            ),
            cls.TASK_FIRST_COMMISSION: (
                u'恭喜您成交了第一个订单！\n',
                u'\n下一个任务：快去成交您的第一个订单吧！首单奖励额外5元！完成新手任务还有10元奖金等你哦！点击查看教程。',
                'http://mp.weixin.qq.com/s?__biz=MzA5MzQxMzU2Mg==&mid=2650808011&idx=6&sn=7fa3264d223630cc1c3b98eb7785744e',
            ),
        }
        if params:
            header, footer, url = items.get(task_name)
            return header.format(**params), footer, url
        else:
            msg = items.get(task_name)
        return msg

    @classmethod
    def get_task_desc(cls, task_name):
        desc = dict(cls.tasks)
        return desc.get(task_name, None)
