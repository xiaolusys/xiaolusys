import csv
from shopback.items.models import Product,ProductSku
with open('/home/user1/meixqhi/product_sku.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        row = [r.decode('gb2312') for r in row]
        prod,state = Product.objects.get_or_create(outer_id=row[0])
        prod.name  = row[1] if row[2]=='null' else row[2] 
        prod.save()
        sku,state = ProductSku.objects.get_or_create(outer_id=row[3],product=prod)
        sku.properties_alias=row[4]
        sku.save()
