import csv
from shopback.items.models import Product,ProductSku
with open('/home/meixqhi/Desktop/product_cost.csv', 'rb') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in spamreader:
        try:
            row = [r.decode('gbk') for r in row]
            try:
                prod = Product.objects.get(outer_id=row[0])
    #        prod.name  = row[1] if row[2]=='null' else row[2] 
    #        prod.std_purchase_price = row[]
    #        prod.save()
            except:
                pass
            else:
                try:
                    sku= ProductSku.objects.get(outer_id=row[2],product=prod)
                except:
                    pass
                else:
            #        sku.properties_alias=row[4]
                    sku.std_purchase_price = row[4]
                    sku.save()
        except Exception,exc:
            print exc.message
