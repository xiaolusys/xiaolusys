# coding=utf-8
__author__ = 'jishu_zifei.zhong'
import json
from django.test import TestCase
from flashsale.pay.models import Register
from flashsale.restpro.v2.views.verifycode_login import validate_code


class VerifyCodeTestCase(TestCase):
    """
    Run test:
    
    python manage.py test -t . --keepdb flashsale.restpro.tests.test_verify_code
    """
    fixtures = [
        'test.flashsale.verifycode.customer.json',
    ]

    url_cashout_verify_code = '/rest/v2/request_cashout_verify_code'
    url_send_code = '/rest/v2/send_code'
    url_verify_code = '/rest/v2/verify_code'

    def setUp(self):
        self.username = 'test_user'
        self.password = 'test'
        self.client.login(username=self.username, password=self.password)

        self.mobile = "18801806068"
            
    def testRegisterActionSendCode(self):
        action = 'register'
        response = self.client.post(self.url_send_code, {'mobile':self.mobile, 'action':action}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["code"], 2)

    def testRequestVerifyCode(self):
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["code"], 0)
        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(reg.submit_count, 1)
        self.assertEqual(reg.verify_count, 0)

    def testVerifyCodeSuccess(self):
        action = 'bind'
        response = self.client.post(self.url_send_code, {'mobile':self.mobile, 'action':action}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(reg.submit_count, 1)
        verify_code = reg.verify_code
        
        response = self.client.post(self.url_verify_code, {'mobile':self.mobile, 'action':action, 'verify_code':verify_code}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['rcode'], 2)

    def testValidateCode(self):
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["code"], 0)
        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(reg.submit_count, 1)
        self.assertEqual(reg.verify_count, 0)

        v = validate_code(self.mobile, '123456')
        self.assertEqual(v, False)
        
        v = validate_code(self.mobile, reg.verify_code)
        self.assertEqual(v, True)
        
        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(reg.submit_count, 0)
        self.assertEqual(reg.verify_count, 1)
        self.assertEqual(reg.verify_code, '')
        
    def testReachDailyLimit(self):
        from flashsale.restpro.v2.views.verifycode_login import MAX_DAY_LIMIT
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        
        reg = Register.objects.filter(vmobile=self.mobile).first()
        reg.submit_count = MAX_DAY_LIMIT
        reg.save()
        
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(data["code"], 4)
        
    def sendTooFrequent(self, sleep_time=1):
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["code"], 0)
        reg = Register.objects.filter(vmobile=self.mobile).first()
        self.assertEqual(reg.submit_count, 1)
        self.assertEqual(reg.verify_count, 0)        

        import time
        time.sleep(sleep_time)
        response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        from flashsale.restpro.v2.views.verifycode_login import RESEND_TIME_LIMIT
        if sleep_time < RESEND_TIME_LIMIT:
            self.assertEqual(data["code"], 5)
        else:
            verify_code = Register.objects.filter(vmobile=self.mobile).first().verify_code
            self.assertEqual(verify_code, reg.verify_code)
        
    def testSendTooFrequentSleep1(self):
        self.sendTooFrequent(1)

    #def testSendTooFrequentSleep170(self):
    #    # only test in local, not on staging or alpha, because it takes 3 minutes.
    #    self.sendTooFrequent(170)
    #
    #def testSendTooFrequentSleep181(self):
    #    # only test in local, not on staging or alpha, because it takes 3 minutes.
    #    self.sendTooFrequent(181)
    #    import time
    #    time.sleep(10)
    #    response = self.client.post(self.url_cashout_verify_code, {}, ACCEPT='application/json')
    #    self.assertEqual(response.status_code, 200)
    #    data = json.loads(response.content)
    #    self.assertEqual(data["code"], 5)
                
