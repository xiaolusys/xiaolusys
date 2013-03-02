import csv
from shopback.items.models import OnlineProduct,OnlineProductSku
with open('/home/user1/meixqhi/product_sku.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        row = [r.decode('gb2312') for r in row]
        prod,state = OnlineProduct.objects.get_or_create(outer_id=row[0])
        prod.name  = row[1] if row[2]=='null' else row[2] 
        prod.save()
        sku,state = OnlineProductSku.objects.get_or_create(outer_id=row[3],prod_outer_id=row[0],product=prod)
        sku.properties_name=row[4]
        sku.save()
