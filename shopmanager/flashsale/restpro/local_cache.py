# coding: utf-8
from common import cacheable
from qiniu import urlsafe_base64_encode

class ImageWaterMarkCache(cacheable.LocalCacheable):
    WATERMARK_TPL = 'watermark/1/image/%s/dissovle/50/gravity/NorthWest/ws/0.382'

    def __init__(self):
        super(ImageWaterMarkCache, self).__init__()
        self.qs = ''

    def load(self):
        from shopback.items.models import ImageWaterMark
        rows = ImageWaterMark.objects.filter(status=1).order_by('-update_time')
        if not rows:
            self.watermark_url = ''
            return
        self.watermark_url = rows[0].url

    @property
    @cacheable.LocalCacheable.reload
    def latest_qs(self):
        if not self.watermark_url:
            return ''
        return self.WATERMARK_TPL % urlsafe_base64_encode(self.watermark_url)

image_watermark_cache = ImageWaterMarkCache()
