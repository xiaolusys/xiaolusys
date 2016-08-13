
from flashsale.xiaolumm.models.models import XiaoluMama

def get_mama_customer(mama_id):
    mama = XiaoluMama.objects.filter(id=mama_id).first()
    return mama.get_mama_customer()
