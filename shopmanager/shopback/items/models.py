#encoding: utf8
from django.db import models
from shopback.base.models import BaseModel
from shopback.base.fields import BigIntegerAutoField

ONSALE_STATUS  = 'onsale'
INSTOCK_STATUS = 'instock'

APPROVE_STATUS  = (
    (ONSALE_STATUS,'出售中'),
    (INSTOCK_STATUS,'库中'),
)


class Item(models.Model):

    num_iid = models.CharField(primary_key=True,max_length=64,blank=False)

    outer_id = models.CharField(max_length=64,blank=True)
    num = models.IntegerField(null=True)

    seller_cids = models.CharField(max_length=126,blank=True)
    approve_status = models.CharField(max_length=20,choices=APPROVE_STATUS,blank=True)  # onsale,instock
    type = models.CharField(max_length=12,blank=True)
    valid_thru = models.IntegerField(null=True)

    cid        = models.BigIntegerField(null=True)
    price      = models.CharField(max_length=12,blank=True)
    postage_id = models.BigIntegerField(null=True)

    has_showcase = models.BooleanField(default=False)
    modified     = models.DateTimeField(null=True,blank=True)

    user_id     = models.CharField(max_length=32,blank=True)
    nick        = models.CharField(max_length=64,blank=True)
    list_time   = models.DateTimeField(null=True,blank=True)
    delist_time = models.DateTimeField(null=True,blank=True)

    has_discount = models.BooleanField(default=False)

    props = models.CharField(max_length=500,blank=True)
    title = models.CharField(max_length=148,blank=True)

    has_invoice = models.BooleanField(default=False)
    pic_url     = models.URLField(verify_exists=False)
    detail_url  = models.URLField(verify_exists=False)

    desc = models.CharField(max_length=64)
    skus = models.CharField(max_length=5000,blank=True)

    status = models.BooleanField(default=True)
    class Meta:
        db_table = 'shop_item'


    def __unicode__(self):
        return self.num_iid+'---'+self.outer_id+'---'+self.title

    @classmethod
    def save_item_through_dict(cls,user_id,item_dict):
        item,state = cls.objects.get_or_create(num_iid = item_dict['num_iid'])
        item.user_id = user_id

        for k,v in item_dict.iteritems():
            hasattr(item,k) and setattr(item,k,v)

        item.save()
        return item



class Product(models.Model):

    outer_id     = models.CharField(max_length=64,primary_key=True)
    name         = models.CharField(max_length=64,blank=True)


    created      = models.DateTimeField(blank=True)
    modified     = models.DateTimeField(blank=True)

    cid          = models.IntegerField(blank=True,null=True)
    cat_name     = models.CharField(max_length=32,blank=True)

    collect_num  = models.IntegerField(null=True)
    price        = models.CharField(max_length=10,blank=True)

#    product_id   = BigIntegerAutoField(primary_key=True)
#    inner_name   = models.CharField(max_length=64,blank=True)

#    tsc          = models.CharField(max_length=32,blank=True)
#    props        = models.CharField(max_length=500,blank=True)
#    props_str    = models.CharField(max_length=500,blank=True)
#
#    binds        = models.CharField(max_length=500,blank=True)
#    binds_str    = models.CharField(max_length=500,blank=True)
#
#    sale_props     = models.CharField(max_length=500,blank=True)
#    sale_props_str = models.CharField(max_length=500,blank=True)

#    desc         = models.TextField(max_length=25000,blank=True)
#    pic_url      = models.CharField(max_length=256,blank=True)
#
#    product_imgs = models.CharField(max_length=1000,blank=True)
#    product_prop_imgs = models.CharField(max_length=2000,blank=True)
#
#    pic_path     = models.CharField(max_length=256,blank=True)
#    vertical_market = models.IntegerField(null=True)
#    customer_props  = models.CharField(max_length=500,blank=True)
#    property_alias  = models.CharField(max_length=1000,blank=True)
#
#    level        = models.IntegerField(null=True)
#    status       = models.IntegerField(null=True)


    class Meta:
        db_table = 'shop_product'



class ProductSku(models.Model):

    outer_id = models.CharField(max_length=64,primary_key=True)

    product  = models.ForeignKey(Product,related_name='skus')

    quantity = models.IntegerField(null=True)

    properties_name = models.CharField(max_length=3000,blank=True)
    properties      = models.CharField(max_length=2000,blank=True)

    status   = models.CharField(max_length=10,blank=True)  #normal,delete

    class Meta:
        db_table = 'shop_productsku'
