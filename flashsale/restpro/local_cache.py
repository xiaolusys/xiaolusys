# coding: utf-8
from django.core.cache import cache

from common import cacheable
from qiniu import urlsafe_base64_encode


class ImageWaterMarkCache(cacheable.LocalCacheable):

    WATERMARK_TPL = 'watermark/1/image/%s/dissovle/50/gravity/Center/dx/0/dy/0/ws/1'
    cache_key = '%s.%s' % (__name__, 'ImageWaterMarkCache')
    cache_time = 0 # 30 * 50

    def __init__(self):
        super(ImageWaterMarkCache, self).__init__()

    # def load(self):
    #     from shopback.items.models import ImageWaterMark
    #     rows = ImageWaterMark.objects.filter(status=1).order_by('-update_time')
    #     if not rows:
    #         self.watermark_url = ''
    #         return
    #     self.watermark_url = rows[0].url

    @property
    # @cacheable.LocalCacheable.reload
    def latest_qs(self):
        cache_value = cache.get(self.cache_key)
        if not cache_value:
            from shopback.items.models import ImageWaterMark
            # TODO@meron cache失效应过期
            water_mark = ImageWaterMark.objects.filter(status=ImageWaterMark.NORMAL)\
                .order_by('-update_time').first()

            if water_mark:
                cache_value = self.WATERMARK_TPL % urlsafe_base64_encode(water_mark.url)
            cache.set(self.cache_key, cache_value, self.cache_time)

        return cache_value

image_watermark_cache = ImageWaterMarkCache()
