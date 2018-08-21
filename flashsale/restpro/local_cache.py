# coding: utf-8
from django.core.cache import cache
from shopback.items.models.storage import ImageWaterMark

def get_image_watermark_cache(mark_size=-1):
    """
    :param mark_size: -1,表示原始大小; 200, 表示按200缩放
    :return:
    """
    return ImageWaterMark.get_global_watermark_op(mark_size=mark_size)
