# coding=utf-8
from __future__ import unicode_literals, absolute_import
from ...models import PotentialMama

__ALL__ = [
    'get_potential_mama_by_mama_id',
    'create_potential_mama',
    'update_potential_by_deposit',
]


def get_potential_mama_by_mama_id(mama_id):
    # type: (int) -> Optional[PotentialMama]
    return PotentialMama.objects.filter(potential_mama=mama_id).first()


def create_potential_mama(mama, referrer_mama_id):
    # type: (XiaoluMama, int) -> PotentialMama
    """创建潜在妈妈记录
    """
    if not referrer_mama_id:
        referrer_mama_id = mama.get_fans_referrer_mama_id()
    customer = mama.get_customer()
    nick = customer.nick if customer else ''
    thumbnail = customer.thumbnail if customer else ""
    potential_mama = PotentialMama.objects.filter(potential_mama=mama.id)
    if not potential_mama:
        uni_key = PotentialMama.gen_uni_key(mama.id, referrer_mama_id)
        potential_mama = PotentialMama(
            potential_mama=mama.id,
            referal_mama=referrer_mama_id,
            nick=nick,
            thumbnail=thumbnail,
            uni_key=uni_key)
        potential_mama.save()
    return potential_mama


def update_potential_by_deposit(mama_id, last_renew_type, referrer_mama_id=None, oid=None, cashout_id=None):
    # type: (int, int, int, Optional[text_type]) -> None
    """由押金订单更新潜在妈妈记录信息
    """
    potential_mama = get_potential_mama_by_mama_id(mama_id)
    if potential_mama:
        return
    extra = {} if not isinstance(potential_mama.extra, dict) else potential_mama.extra
    if oid:
        extra.update({"oid": oid})
    if cashout_id:
        extra.update({"cashout_id": cashout_id})
    potential_mama.extras = extra
    update_fields = [extra]
    if potential_mama.last_renew_type != last_renew_type:
        potential_mama.last_renew_type = last_renew_type
        update_fields.append('last_renew_type')
    if not potential_mama.is_full_member:
        potential_mama.is_full_member = True
        update_fields.append('is_full_member')
    if referrer_mama_id and potential_mama.referal_mama != referrer_mama_id:
        potential_mama.referal_mama = referrer_mama_id
        update_fields.append('referal_mama')
    if update_fields:
        potential_mama.save(update_fields=update_fields)
    return
