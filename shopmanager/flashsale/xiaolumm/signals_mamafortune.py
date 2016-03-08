from django.db.models.signals import post_save
from flashsale.xiaolumm import tasks_mama
from flashsale.xiaolumm.modes_fortune import CarryRecord,OrderCarry,AwardCarry,ClickCarry



def ordercarry_update_carryrecord(sender, instance, created, **kwargs):
    carryrecord_type = 2 # order carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()

    if instance.is_direct_or_fans_carry():
        # find out parent mama_id
        raltionships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id)
        if relationships.count() > 0:
            parent_mama_id = relationships[0].mama_id
            tasks_mama.update_second_level_ordercarry.s(parent_mama_id, instance)()
        

post_save.connect(ordercarry_update_carryrecord,
                  sender=OrderCarry, dispatch_uid='post_save_order_carry')



def awardcarry_update_carryrecord(sender, instance, created, **kwargs):
    carryrecord_type = 3 # award carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()


post_save.connect(awardcarry_update_carryrecord,
                  sender=AwardCarry, dispatch_uid='post_save_award_carry')


def clickcarry_update_carryrecord(sender, instance, created, **kwargs):
    tasks_mama.update_carryrecord_carry_num.s(instance)()


post_save.connect(clickcarry_update_carryrecord,
                  sender=ClickCarry, dispatch_uid='post_save_click_carry')
    
