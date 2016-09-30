# -*- coding:utf8 -*-
from  StringIO import StringIO
import urllib, urllib2
from lxml import etree
from shopapp.smsmgr.models import SMSRecord, SMSPlatform
from shopapp.smsmgr.sensitive_word import sensitive_words
from shopback.base.exception import NotImplement
from shopback import paramconfig as pcfg
import logging

logger = logging.getLogger('django.request')


class SMSManager():
    """ 短信收发管理器接口 """

    _platform = None  # 短信服务商名称

    def create_record(self, mobiles, task_name, task_type, content):
        """ 创建短信发送记录 """
        smsrecord = SMSRecord.objects.create(
            platform=SMSPlatform.objects.get(code=self._platform),
            task_id='',
            task_name=task_name,
            task_type=task_type,
            mobiles=mobiles,
            content=content,
            countnums=len(mobiles.split(',')),
            status=pcfg.SMS_CREATED)
        return smsrecord

    def batch_send(self, *args, **kwargs):
        """ 批量发送短信接口方法 """
        raise NotImplement("该方法没有实现")

    def check_status(self, *args, **kwargs):
        """ 检查任务执行状态 """
        raise NotImplement("该方法没有实现")

    def check_content(self, *args, **kwargs):
        """ 验证短信内容 """
        return False


class CSHXSMSManager(SMSManager):
    """ 创世华信短信发送接口实现 """
    _platform = 'cshx'
    _sms_url = 'http://121.52.220.246:8888/sms.aspx'
    _status_url = 'http://121.52.220.246:8888/statusApi.aspx'

    def batch_send(self, *args, **kwargs):
        """ 批量发送短信接口实现
            res_content      = '<?xml version="1.0" encoding="utf-8" ?>
                    <returnsms>
                        <returnstatus>Success</returnstatus>
                        <message>ok</message>
                        <remainpoint>58001</remainpoint>
                        <taskID>132668</taskID>
                        <successCounts>1</successCounts>
                    </returnsms>'
        """

        fields = ['userid', 'account', 'password', 'mobile', 'taskName', 'content',
                  'sendtime', 'mobilenumber', 'countnumber', 'telephonenumber', 'checkcontent']

        params = {}
        for f in fields:
            if kwargs.has_key(f):
                params[f] = kwargs[f]

        params['action'] = 'send'

        response = ''
        success = False
        task_id = None
        succnums = 0
        res_content = ''
        try:
            for k, v in params.items():
                if isinstance(v, unicode):
                    params[k] = v.encode('utf8')

            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            status = tree.xpath('/returnsms/returnstatus')[0].text
            success = status.lower() == 'success'
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
        else:
            task_id = tree.xpath('/returnsms/taskID')[0].text
            succnums = tree.xpath('/returnsms/successCounts')[0].text

        return success, task_id, succnums, res_content

    def check_content(self, *args, **kwargs):
        """ 创世华信短信非法关键词查询 """

        params = {}
        params['userid'] = kwargs.get('userid', '')
        params['account'] = kwargs.get('account', '')
        params['password'] = kwargs.get('password', '')
        params['content'] = kwargs.get('content', '')
        params['action'] = 'checkkeyword'

        msg = ''
        try:
            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            msg = tree.xpath('/returnsms/message')[0].text
        except Exception, exc:
            msg = exc.message

        return msg


class IPYYSMSManager(SMSManager):
    """ 创世华信短信发送接口实现 """
    _platform = 'ipyy'
    _sms_url = 'http://sh2.ipyy.com/sms.aspx'
    _status_url = 'http://sh2.ipyy.com/statusApi.aspx'

    def batch_send(self, *args, **kwargs):
        """ 批量发送短信接口实现
            res_content      = '<?xml version="1.0" encoding="utf-8" ?>
                    <returnsms>
                        <returnstatus>Success</returnstatus>
                        <message>ok</message>
                        <remainpoint>58001</remainpoint>
                        <taskID>132668</taskID>
                        <successCounts>1</successCounts>
                    </returnsms>'
        """

        fields = ['userid', 'account', 'password', 'mobile', 'taskName', 'content',
                  'sendtime', 'mobilenumber', 'countnumber', 'telephonenumber', 'checkcontent']

        params = {}
        for f in fields:
            if kwargs.has_key(f):
                v = kwargs[f]
                if f == 'content':
                    v = u'【小鹿美美】'+ v.replace(u'【小鹿美美】', u'')
                params[f] = v

        params['action'] = 'send'
        response = ''
        success = False
        task_id = None
        succnums = 0
        res_content = ''
        try:
            for k, v in params.items():
                if isinstance(v, unicode):
                    params[k] = v.encode('utf8')

            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            status = tree.xpath('/returnsms/returnstatus')[0].text
            success = status.lower() == 'success'
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
        else:
            task_id = tree.xpath('/returnsms/taskID')[0].text
            succnums = tree.xpath('/returnsms/successCounts')[0].text

        return success, task_id, succnums, res_content

    def check_content(self, *args, **kwargs):
        """ 创世华信短信非法关键词查询 """

        params = {}
        params['userid'] = kwargs.get('userid', '')
        params['account'] = kwargs.get('account', '')
        params['password'] = kwargs.get('password', '')
        params['content'] = kwargs.get('content', '')
        params['action'] = 'checkkeyword'

        msg = ''
        try:
            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            msg = tree.xpath('/returnsms/message')[0].text
        except Exception, exc:
            msg = exc.message

        return msg


class DXTSMSManager(SMSManager):
    """ 短信通591短信发送接口实现 """
    _platform = 'dxt'
    _sms_url = 'http://www.591duanxin.com/sms.aspx'
    _status_url = 'http://www.591duanxin.com/statusApi.aspx'

    def batch_send(self, *args, **kwargs):
        """ 批量发送短信接口实现
            res_content      = '<?xml version="1.0" encoding="utf-8" ?>
                    <returnsms>
                        <returnstatus>Success</returnstatus>
                        <message>ok</message>
                        <remainpoint>58001</remainpoint>
                        <taskID>132668</taskID>
                        <successCounts>1</successCounts>
                    </returnsms>'
        """

        fields = ['userid', 'account', 'password', 'mobile', 'content',
                  'sendtime', 'action', 'extno']

        params = {}
        for f in fields:
            if kwargs.has_key(f):
                params[f] = kwargs[f]

        params['action'] = 'send'

        response = ''
        success = False
        task_id = None
        succnums = 0
        res_content = ''
        try:
            for k, v in params.items():
                if isinstance(v, unicode):
                    params[k] = v.encode('utf8')

            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            status = tree.xpath('/returnsms/returnstatus')[0].text
            success = status.lower() == 'success'
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
        else:
            task_id = tree.xpath('/returnsms/taskID')[0].text
            succnums = tree.xpath('/returnsms/successCounts')[0].text

        return success, task_id, succnums, res_content

    def check_content(self, *args, **kwargs):
        """ 短信通591短信非法关键词查询 """

        params = {}
        params['userid'] = kwargs.get('userid', '')
        params['account'] = kwargs.get('account', '')
        params['password'] = kwargs.get('password', '')
        params['action'] = 'checkkeyword'

        msg = ''
        try:
            encode_params = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, encode_params, 60)
            res_content = response.read()

            parser = etree.XMLParser()
            tree = etree.parse(StringIO(res_content.strip()), parser)
            msg = tree.xpath('/returnsms/message')[0].text
        except Exception, exc:
            msg = exc.message

        return msg


class SYKJSMSManager(SMSManager):
    """
    示远科技短信发送接口实现
    """
    _platform = '18sms'
    _sms_url = 'http://send.18sms.com/msg/HttpBatchSendSM'

    def batch_send(self, *args, **kwargs):
        """
        批量发送短信接口实现
        - account
        - pswd
        - mobile
        - msg
        - needstatus:true
        - extno:3106
        """

        mobile = kwargs.get('mobile', '')
        content = self.filter_content(kwargs.get('content', ''))

        params = {
            'account': kwargs.get('account', ''),
            'pswd': kwargs.get('password', ''),
            'mobile': mobile,
            'msg': content,
            'needstatus': 'true',
            'extno': '3106'
        }

        response = ''
        success = False
        task_id = None
        succnums = 0
        content = ''
        try:
            data = urllib.urlencode(params)
            response = urllib2.urlopen(self._sms_url, data, 60)
            content = response.read()

            lines = content.split()
            line1 = lines[0]
            if len(lines) == 2:
                task_id = lines[1]
            timestamp, status_code = line1.split(',')
            if status_code == '0':
                success = True
            else:
                success = False
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
        else:
            succnums = 1

        return success, task_id, succnums, content

    def filter_content(self, content):
        for word in sensitive_words:
            if content.find(word) > 0:
                content = content.replace(word, '**')
        return content


SMS_CODE_MANAGER_TUPLE = (
    ('cshx', CSHXSMSManager),
    ('dxt', DXTSMSManager),
    ('ipyy', IPYYSMSManager),
    ('18sms', SYKJSMSManager),
)
