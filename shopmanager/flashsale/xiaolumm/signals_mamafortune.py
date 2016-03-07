
from flashsale.xiaolumm.modes_fortune import CarryRecord,OrderCarry,AwardCarry,ClickCarry



def carryrecord_creation_update_mamafortune(sender, instance, created, **kwargs):
    """
    post_save signal only deal with creation
    """
    if not created:
        return 
    
    mama_id = instance.mama_id
    amount  = instance.carry_num

    if instance.is_click_carry():
        # dont do anything
        return
    
    if instance.is_award_carry() and instance.is_carry_confirmed():
        # award carry has to be confirmed on creation
        action_key = "32" # increment both cash and carry
        tasks_mama.increment_mamafortune_carry.s(mama_id, amount, action_key)()
        return
    
    if instance.is_order_carry():
        if instance.is_carry_pending():
            action_key = "31" # increment carry only
        if instance.is_carry_confirmed(): 
            action_key = "32" # increment cash and carry
        tasks_mama.increment_mamafortune_carry.s(mama_id, amount, action_key)()
        return


signals.post_save.connect(carryrecord_creation_update_mamafortune, 
                          sender=CarryRecord, dispatch_uid='post_save_carry_record')



def ordercarry_update_carryrecord(sender, instance, created, **kwargs):
    carryrecord_type = 2 # order carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()

    if instance.is_direct_or_fans_carry():
        # find out parent mama_id
        raltionships = ReferalRelationship.objects.filter(referal_to_mama_id=instance.mama_id)
        if relationships.count() > 0:
            parent_mama_id = relationships[0].mama_id
            tasks_mama.update_second_level_ordercarry.s(parent_mama_id, instance)()
        

signals.post_save.connect(ordercarry_update_carryrecord,
                          sender=OrderCarry, dispatch_uid='post_save_order_carry')



def awardcarry_update_carryrecord(sender, instance, created, **kwargs):
    carryrecord_type = 3 # award carry
    tasks_mama.update_carryrecord.s(instance, carryrecord_type)()


signals.post_save.connect(awardcarry_update_carryrecord,
                          sender=AwardCarry, dispatch_uid='post_save_award_carry')
    

def clickcarry_update_carryrecord(sender, instance, created, **kwargs):
    tasks_mama.update_carryrecord_carry_num.s(instance)()


signals.post_save.connect(clickcarry_update_carryrecord,
                          sender=ClickCarry, dispatch_uid='post_save_click_carry')
    
