# encoding=utf8
import os
import sys
sys.path.append('.')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shopmanager.settings")
from flashsale.xiaolumm.models.models_fortune import ReferalRelationship
from pymongo import MongoClient


db = MongoClient('0.0.0.0:32769').xlmm


if __name__ == '__main__':
    import django
    django.setup()

    # items = ReferalRelationship.objects.using('product').all().values('referal_from_mama_id', 'referal_to_mama_id')

    # for item in items:
    #     from_id = str(item['referal_from_mama_id'])
    #     to_id = str(item['referal_to_mama_id'])
    #     db.tuijian.insert({
    #         'from_id': from_id,
    #         'to_id': to_id,
    #     })

    # items = db.tuijian.find()
    # for item in items:
    #     print item['from_id']

    def print_children(id, level):
        items = db.tuijian.find({'from_id': id})
        children = [x['to_id'] for x in items]

        print '--'*level, level, id
        if children:
            for child in children:
                print_children(child, level+1)
        else:
            return

    print_children('320', 0)
