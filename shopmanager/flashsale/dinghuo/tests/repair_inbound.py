inbounds = InBound.objects.filter(status=3)
for i in inbounds.filter(out_stock=False):
...     if i.all_arrival_quantity > i.all_allocate_quantity:
...         inbounds_out_stocks.append(i)
for i in inbounds_out_stocks:
...     for detail in i.details.all():
...         detail.reset_out_stock()
...
>>> for i in inbounds_out_stocks:
...     if i.set_stat():
...         i.save()