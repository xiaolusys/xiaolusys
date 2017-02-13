# coding: utf8
from __future__ import absolute_import, unicode_literals

from django.db import IntegrityError

from shopback.items.models import ProductSku
from ..models import StockBatchFlowRecord

def get_or_create_stock_batch_record(sku_id, record_num, batch_no, referal_id, record_type, row_split=False):
    psku = ProductSku.objects.get(id=sku_id)
    model_id = psku.product.model_id
    uni_key = '%s-%s' % (referal_id, record_type)
    if row_split:
        first_record = StockBatchFlowRecord.objects.filter(uni_key__startswith=uni_key).order_by('uni_key').first()
        if first_record:
            split_list = first_record.uni_key.split('-')
            uni_key = len(split_list) > 2 and '%s-%s'%(uni_key, int(split_list[2]) + 1) or '%s-%s'%(uni_key, 1)

    try:
        record = StockBatchFlowRecord.objects.create(
            model_id=model_id,
            sku_id=sku_id,
            record_num=record_num,
            batch_no=batch_no,
            record_type=record_type,
            referal_id=referal_id,
            uni_key=uni_key,
        )
    except IntegrityError:
        record = StockBatchFlowRecord.objects.get(uni_key=uni_key)
    return record

def push_saleorder_post_batch_record(sku_id, record_num, batch_no, referal_id, row_split=False):
    return get_or_create_stock_batch_record(
        sku_id, record_num, batch_no, referal_id, StockBatchFlowRecord.SALEORDER, row_split=row_split)

def push_salerefund_post_batch_record(sku_id, record_num, batch_no, referal_id):
    return get_or_create_stock_batch_record(
        sku_id, record_num, batch_no, referal_id, StockBatchFlowRecord.SALEREFUND)

def set_stock_batch_flow_record_finished(referal_id, record_type):
    uni_key = '%s-%s' % (referal_id, record_type)
    records = StockBatchFlowRecord.objects.filter(uni_key__startswith=uni_key, status=False)
    for record in records:
        record.as_finished()
        record.save()