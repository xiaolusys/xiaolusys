from shopback.trades.models import MergeTrade,MergeOrder

mgo = MergeOrder.objects.filter(merge_trade__user=None)
print mgo.count()
for o in mgo:
    o.delete()

mgt = MergeTrade.objects.filter(user=None)
print mgt.count()
for m in mgt:
    m.delete()

mts = MergeTrade.objects.filter(tid='')
mts.count()

index = 10001
oindex = 10001
for m in mts:
    m.tid = 'HYD%d'%index
    m.save()
    index = index+1
    
mos = MergeOrder.objects.filter(oid='')
for o in mos:
    o.oid = 'HYO%d'%oindex
    o.save()
    oindex = oindex+1
