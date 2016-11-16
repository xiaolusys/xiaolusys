# coding: utf8

from django.test import TestCase
from core.upload.upload import upload_public_to_remote

class QiniuUploadTestCase(TestCase):

    fixtures = []

    def testUpload(self):
        upload_public_to_remote('mediaroom', 'qrcode/4392113f9eb637827f6061bf1e86b0ec.jpg')