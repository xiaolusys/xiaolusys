# conding=utf-8
from flashsale.pay.models_addr import UserAddress

print UserAddress.objects.filter(id='0').count()
def repair_id():
    last_id = UserAddress.objects.order_by('-id')[0].id
    now_id = last_id + 1
    need_changes = UserAddress.objects.filter(id='0').order_by('created')
    for ua in need_changes:
        print now_id
        new_ua = copy_from_ua(ua)
        ua.delete()
        new_ua.id = now_id
        new_ua.save()
        now_id +=1


def copy_from_ua(ua):
    new_ua = UserAddress()
    attrs = ['cus_uid', 'receiver_name', 'receiver_state', 'receiver_city', 'receiver_district', 'receiver_address',
             'receiver_zip', 'receiver_mobile', 'receiver_phone', 'default', 'status', 'created']
    for attr in attrs:
        setattr(new_ua,attr,getattr(ua,attr))
    return new_ua

