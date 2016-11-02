# coding: utf-8

import datetime
import json
import sys

from django import forms

from core.forms import BaseForm
from apis.v1.products import ProductCtl, SkustatCtl

from .models import Product, ProductSku
from . import constants


class ProductSkuFormset(forms.models.BaseInlineFormSet):
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=None, **kwargs):
        if instance is None:
            self.instance = self.fk.rel.to()
        else:
            self.instance = instance
        self.save_as_new = save_as_new
        if queryset is None:
            queryset = self.model._default_manager
        if self.instance.pk is not None:
            qs = queryset.filter(**{self.fk.name: self.instance})
        else:
            qs = queryset.none()
        print 'queryset', qs.count()
        for sku in qs:
            api_skustat = SkustatCtl.retrieve(sku.id)
            sku.quantity = api_skustat.get_realtime_quantity()
            sku.wait_post_num = api_skustat.get_wait_post_num()
            sku.lock_num = api_skustat.get_lock_num()

        # BaseInlineFormSet, self).__init__(data, files, prefix=prefix,
        #                                         queryset=qs, **kwargs)
        forms.BaseModelFormSet.__init__(self, data, files, prefix=prefix,
                                                queryset=qs, **kwargs)


class ProductModelForm(forms.ModelForm):
    pic_path = forms.CharField(
        label=u'图片链接',
        widget=forms.TextInput(attrs={'size': '60',
                                      'maxlength': '256'}))

    class Meta:
        model = Product
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(ProductModelForm, self).__init__(*args, **kwargs)
        api_product = ProductCtl.retrieve(self.instance.id)
        self.initial['collect_num'] = api_product.get_realtime_quantity()
        self.initial['wait_post_num'] =  api_product.get_wait_post_num()
        self.initial['lock_num'] = api_product.get_lock_num()


class ProductLocationForm(BaseForm):
    product = forms.IntegerField()
    sku = forms.IntegerField(required=False)
    district = forms.CharField()

    # product = forms.IntegerField(choices=Product.objects.all())
    # sku = forms.ChoiceField(choices=ProductSku.objects.all(), required=False)
    # district = forms.ChoiceField(choices=DepositeDistrict.objects.all())
    # product = forms.ModelChoiceField(Product.objects)
    # sku = forms.ModelChoiceField(ProductSku.objects, required=False)
    # district = forms.ModelChoiceField(DepositeDistrict.objects)


class ProductScanForm(forms.Form):
    wave_no = forms.CharField(max_length=32, required=True)
    barcode = forms.CharField(max_length=32, required=True)
    num = forms.IntegerField(min_value=1, max_value=10000, required=True)


class ProductScheduleForm(BaseForm):
    onshelf_datetime_start = forms.DateTimeField(required=False)
    onshelf_datetime_end = forms.DateTimeField(required=False)
    offshelf_datetime_start = forms.DateTimeField(required=False)
    offshelf_datetime_end = forms.DateTimeField(required=False)
    onshelf_date = forms.DateField(required=False)
    is_watermark = forms.BooleanField(required=False)
    is_not_watermark = forms.BooleanField(required=False)
    is_seckill = forms.BooleanField(required=False)
    is_not_seckill = forms.BooleanField(required=False)
    category_id = forms.IntegerField(required=False, initial=0)
    price = forms.FloatField(required=False)
    model_id = forms.CharField(required=False)
    warehouse_id = forms.IntegerField(required=False)
    rebeta_schema_id = forms.IntegerField(required=False)
    schedule_ids = forms.CharField(required=False, initial='[]')
    product_ids = forms.CharField(required=False, initial='[]')
    sale_type = forms.TypedChoiceField(required=False,
                                       coerce=int,
                                       choices=constants.SALE_TYPES)
    to_schedule = forms.TypedChoiceField(required=False,
                                         coerce=int,
                                         choices=((0, u'不排期'), (1, u'排期')),
                                         initial=0)

    def has_schedule_params(self):
        schedule_param_fields = ['onshelf_datetime_start',
                                 'onshelf_datetime_end',
                                 'offshelf_datetime_start',
                                 'offshelf_datetime_end', 'onshelf_date']
        for f in schedule_param_fields:
            if getattr(self.cleaned_attrs, f, None):
                return True
        return False

    def has_schedule_update_kwargs(self):
        schedule_param_fields = ['onshelf_datetime_start',
                                 'onshelf_datetime_end',
                                 'offshelf_datetime_start',
                                 'offshelf_datetime_end']
        for f in schedule_param_fields:
            if getattr(self.cleaned_attrs, f, None):
                return True
        return False

    def is_empty(self):
        for f in self.fields.keys():
            v = getattr(self.cleaned_attrs, f, None)
            if f in ['warehouse_id']:
                if v != None:
                    return False
            else:
                if v:
                    return False
        return True

    def get_product_query(self):
        from . import local_cache
        q = {}
        ca = self.cleaned_attrs
        product_ids = json.loads(ca.product_ids)
        if product_ids:
            q['pk__in'] = product_ids
        else:
            if ca.is_watermark:
                q['is_watermark'] = 1
            if ca.is_seckill:
                q['is_seckill'] = 1
            if ca.category_id:
                q['category_id'] = ca.category_id
            else:
                q['category_id__in'] = map(
                    lambda x: x['id'],
                    local_cache.product_category_cache.categories)
            if ca.warehouse_id != None:
                q['ware_by'] = ca.warehouse_id
            if ca.model_id:
                q['model_id'] = ca.model_id
        q['status'] = Product.NORMAL
        return q

    def get_schedule_query(self):
        from . import local_cache
        q = {}
        ca = self.cleaned_attrs
        schedule_ids = json.loads(ca.schedule_ids)
        if schedule_ids:
            q['pk__in'] = schedule_ids
        else:
            pq = self.get_product_query()
            for k, v in pq.iteritems():
                q['product__%s' % k] = v
            if ca.onshelf_date:
                q['onshelf_datetime__lte'] = datetime.datetime.combine(
                    ca.onshelf_date, datetime.datetime.min.time())
                q['offshelf_datetime__gte'] = datetime.datetime.combine(
                    ca.onshelf_date, datetime.datetime.min.time())
            else:
                if ca.onshelf_datetime_start:
                    if not ca.onshelf_datetime_end:
                        q['onshelf_datetime'] = ca.onshelf_datetime_start
                    else:
                        q['onshelf_datetime__gte'] = ca.onshelf_datetime_start
                        q['onshelf_datetime__lte'] = ca.onshelf_datetime_end
                if ca.offshelf_datetime_start:
                    if not ca.offshelf_datetime_end:
                        q['offshelf_datetime'] = ca.offshelf_datetime_start
                    else:
                        q['offshelf_datetime__gte'] = ca.offshelf_datetime_start
                        q['offshelf_datetime__lte'] = ca.offshelf_datetime_end
        return q

    def get_product_update_kwargs(self):
        kwargs = {}
        ca = self.cleaned_attrs
        if ca.price:
            kwargs['agent_price'] = ca.price
        if ca.is_watermark:
            kwargs['is_watermark'] = 1
        if ca.is_seckill:
            kwargs['is_seckill'] = 1
        if ca.is_not_watermark:
            kwargs['is_watermark'] = 0
        if ca.is_not_seckill:
            kwargs['is_seckill'] = 0
        return kwargs

    def get_schedule_update_kwargs(self):
        kwargs = {}
        ca = self.cleaned_attrs
        if ca.onshelf_datetime_start and ca.onshelf_datetime_end:
            kwargs.update({
                'onshelf_datetime': ca.onshelf_datetime_start,
                'offshelf_datetime': ca.offshelf_datetime_start
            })
        if ca.sale_type:
            kwargs['sale_type'] = ca.sale_type
        return kwargs

    @property
    def json(self):
        data = self.cleaned_data
        ca = self.cleaned_attrs
        datetime_fields = ['onshelf_datetime_start', 'onshelf_datetime_end',
                           'offshelf_datetime_start', 'offshelf_datetime_end']
        for f in datetime_fields:
            v = getattr(ca, f, None)
            if v:
                data[f] = v.strftime('%Y-%m-%d %H:%M:%S')
        if ca.onshelf_date:
            data['onshelf_date'] = ca.onshelf_date.strftime('%Y-%m-%d')
        return data


class ProductScheduleAPIForm(BaseForm):
    schedule_id = forms.IntegerField(required=False)
    product_id = forms.IntegerField(required=False)
    price = forms.FloatField(required=False)
    type = forms.IntegerField(required=False)
    flag = forms.IntegerField(required=False)
