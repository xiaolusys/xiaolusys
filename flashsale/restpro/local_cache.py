# coding: utf-8
from django.core.cache import cache
from shopback.items.models.storage import ImageWaterMark

def get_image_watermark_cache():
    return ImageWaterMark.get_global_watermark_op()
