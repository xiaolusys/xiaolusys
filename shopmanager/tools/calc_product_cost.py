from shopback.items.models import Product,ProductSku

def calcProductCost(sfile_path,tfile_path):
    
    tfile = open(tfile_path,'w+')
    with open(sfile_path,'r') as sf:
        for s in sf.readlines()[1:]:
            try:
                ss = [r.strip().decode('utf8') for r in s.split(',')]
                if ss[2]:
                    prod_sku = ProductSku.objects.get(outer_id=ss[2],product__outer_id=ss[0])
                    print >> tfile,','.join([ss[0],ss[2],str(prod_sku.quantity),str(prod_sku.cost)])
                elif ss[0]:
                    product = Product.objects.get(outer_id=ss[0])
                    print >> tfile,','.join([ss[0],ss[2],str(product.collect_num),str(product.cost)])
            except:
                print ss
    tfile.close()
