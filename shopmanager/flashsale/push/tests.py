# coding: utf-8

import unittest


from .mipush import mipush_of_ios

REGID = 'd//igwEhgBGCI2TG6lWqlCFEpqvnKBZ8IiQBtpyXE11uw/Wo7N9D3eCESq1YBnLW/0misMINCyXWBZ6OxNNd3/0Z0qZ9DSz9SYk6tKmcaPa+zoTBEdZHS2cdiH1znaxO'

class PushTestCase(unittest.TestCase):
    def test_push_by_regid(self):
        print mipush_of_ios.push_to_regid(REGID, {'target_url': 'v1'}, description='测试推送')
