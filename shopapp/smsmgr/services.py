# -*- coding:utf8 -*-
from __future__ import unicode_literals
import re
import json
import random
from  StringIO import StringIO
import urllib, urllib2
from lxml import etree
from django.db.models import F
from django.conf import settings
from shopapp.smsmgr.models import SMSRecord, SMSPlatform, SMSActivity
from shopapp.smsmgr.sensitive_word import sensitive_words
from shopback.base.exception import NotImplement
from aliapis import AlibabaAliqinFcSmsNumSendRequest

from .models import SMSPlatform, SMS_NOTIFY_ACTIVITY
from shopback import paramconfig as pcfg
import logging
logger = logging.getLogger(__name__)

SMS_PARAMS_PREFIX = 'sms_'
REGEX_PHONE  = '^1[34578][0-9]{9}$'

class SMSManager():
    """ 短信收发管理器接口 """
    _platform = None
    _platform_code = None  # 短信服务商编码
    _support_sms_template_code = False

    def __init__(self):
        self._platform = self.get_smsplateform()

    def get_sms_template(self, msg_type):
        templates = list(SMSActivity.objects.filter(sms_type=msg_type, status=SMSActivity.NORMAL))
        if not templates:
            raise Exception('请输入正确的短信消息类型')
        return random.sample(templates, 1)[0]

    def get_smsplateform(self):
        return SMSPlatform.objects.get(code=self._platform_code)

    def filter_template_params(self, kwargs):
        params = {}
        for k ,v in kwargs.iteritems():
            if k.startswith(SMS_PARAMS_PREFIX):
                params[k] = v
        return params

    def check_and_return_mobiles(self, mobiles):
        if isinstance(mobiles, (str, unicode)):
            mobiles = mobiles.split(',')

        if not isinstance(mobiles, (list, tuple)):
            raise Exception('请输入正确的手机号码列表: %s'% mobiles)

        new_mobiles = []
        check_regex = re.compile(REGEX_PHONE)
        for mobile in mobiles:
            if not mobile:
                continue
            if not check_regex.match(mobile):
                raise Exception('手机号格式不对: %s'% mobile)
            new_mobiles.append(mobile)

        if not new_mobiles:
            raise Exception('请输入正确的手机号码列表不能为空')

        return new_mobiles

    def create_record(self, mobiles, task_name, task_type, content):
        """ 创建短信发送记录 """
        smsrecord = SMSRecord.objects.create(
            platform=self.get_smsplateform(),
            task_id='',
            task_name=task_name,
            task_type=task_type,
            mobiles=mobiles,
            content=content,
            countnums=len(mobiles.split(',')),
            status=pcfg.SMS_CREATED)
        return smsrecord

    def tag_sign_name_if_force(self, content):
        if self._platform.is_force_sign:
            return self._platform.sign_name + re.sub(self._platform.sign_name, '', content)
        return content

    def on_send(self, *args, **kwargs):
        if not settings.SMS_PUSH_SWITCH:
            return
        return self._batch_send(*args, **kwargs)

    def on_success(self, success_count):
        self._platform.sendnums = F('sendnums') + int(success_count)
        self._platform.save(update_fields=['sendnums'])

    def _batch_send(self, mobiles, msg_type, *args, **kwargs):
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
    _platform_code = 'cshx'
    _sms_url = 'http://121.52.220.246:8888/sms.aspx'
    _status_url = 'http://121.52.220.246:8888/statusApi.aspx'

    def _batch_send(self, mobiles, msg_type, **kwargs):
        """ 批量发送短信接口实现
            <?xml version="1.0" encoding="utf-8" ?>
            <returnsms>
                <returnstatus>Success</returnstatus>
                <message>ok</message>
                <remainpoint>58001</remainpoint>
                <taskID>132668</taskID>
                <successCounts>1</successCounts>
            </returnsms>
        """

        sms_tpl = self.get_sms_template(msg_type)
        tpl_params = self.filter_template_params(kwargs)
        sms_content = self.tag_sign_name_if_force(sms_tpl.render_to_message(tpl_params))
        mobiles_str = ','.join(self.check_and_return_mobiles(mobiles))
        params  = {}
        params['userid'] = self._platform.user_id
        params['account'] = self._platform.account
        params['password'] = self._platform.password
        params['mobile'] = mobiles_str
        params['taskName'] = sms_tpl.get_sms_type_display()
        params['mobilenumber'] = 1
        params['countnumber'] = 1
        params['telephonenumber'] = 0
        params['action'] = 'send'
        params['checkcontent'] = '0'
        params['action'] = 'send'
        params['content'] = sms_content

        sms_record = self.create_record(
            mobiles_str,
            sms_tpl.get_sms_type_display(),
            msg_type,
            sms_content
        )
        success = False
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
        except Exception, exc:
            logger.error('%s'%exc, exc_info=True)
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
            logger.error(exc.message, exc_info=True)
        else:
            task_id = tree.xpath('/returnsms/taskID')[0].text
            succnums = tree.xpath('/returnsms/successCounts')[0].text
            success  = status.lower() == 'success'
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = res_content
            sms_record.status = pcfg.SMS_COMMIT or pcfg.SMS_ERROR
            if success:
                self.on_success(succnums)
        sms_record.save()
        return success


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


class IPYYSMSManager(CSHXSMSManager):
    """ 创世华信消息通知短信发送接口实现 """
    _platform_code = 'ipyy'
    _sms_url = 'http://sh2.ipyy.com/sms.aspx'
    _status_url = 'http://sh2.ipyy.com/statusApi.aspx'



class DXTSMSManager(SMSManager):
    """ deprecated
     短信通591短信发送接口实现
     """
    _platform_code = 'dxt'
    _sms_url = 'http://www.591duanxin.com/sms.aspx'
    _status_url = 'http://www.591duanxin.com/statusApi.aspx'

    def _batch_send(self, *args, **kwargs):
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
    """ deprecated
    示远科技短信发送接口实现
    """
    _platform_code = '18sms'
    _sms_url = 'http://send.18sms.com/msg/HttpBatchSendSM'

    def _batch_send(self, *args, **kwargs):
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


class ALIDAYUSMSManager(SMSManager):
    """
        alidayu短信发送接口实现
        {
            u'alibaba_aliqin_fc_sms_num_send_response': {
                u'result': {
                    u'model': u'104652156018^1106479900301',
                    u'success': True,
                    u'err_code': u'0'
                },
                u'request_id': u'45vwf4ymw9kf'
            }
        }
    """
    _platform_code = 'alidayu'
    _sms_url = 'https://eco.taobao.com/router/rest'
    _support_sms_template_code = True

    def _batch_send(self, mobiles, msg_type, **kwargs):
        """
        批量发送短信接口实现
        - account
        - pswd
        - mobile
        - msg
        - needstatus:true
        - extno:3106
        """
        mobiles = self.check_and_return_mobiles(mobiles)
        sms_tpl = self.get_sms_template(msg_type)
        tpl_params = self.filter_template_params(kwargs)
        sms_content = self.tag_sign_name_if_force(sms_tpl.render_to_message(tpl_params))
        mobiles_str = ','.join(mobiles)

        sms_record = self.create_record(
            mobiles_str,
            sms_tpl.get_sms_type_display(),
            msg_type,
            sms_content
        )

        success = False
        sms_template_code = sms_tpl.sms_template_code

        plateform = self._platform
        req = AlibabaAliqinFcSmsNumSendRequest(
            plateform.account,
            plateform.password,
            url=self._sms_url
        )

        # req.extend = "123456"
        req.sms_type = "normal"
        if plateform.is_force_sign:
            req.sms_free_sign_name = plateform.sign_name

        req.sms_param = json.dumps(tpl_params)
        req.rec_num = mobiles_str
        req.sms_template_code = sms_template_code
        try:
            resp = req.getResponse()
            if resp.has_key('error_response'):
                raise Exception('alidayu send message error')
        except Exception, exc:
            logger.error('%s' % exc, exc_info=True)
            sms_record.status = pcfg.SMS_ERROR
            sms_record.memo = exc.message
        else:
            task_id = resp['alibaba_aliqin_fc_sms_num_send_response']['result']['model']
            success = resp['alibaba_aliqin_fc_sms_num_send_response']['result']['success']
            succnums = len(mobiles)
            sms_record.task_id = task_id
            sms_record.succnums = succnums
            sms_record.retmsg = json.dumps(resp)
            sms_record.status = success and pcfg.SMS_COMMIT or pcfg.SMS_ERROR
            if success:
                self.on_success(succnums)
        sms_record.save()
        return success


SMS_CODE_MANAGER_TUPLE = (
    ('cshx', CSHXSMSManager),
    ('dxt', DXTSMSManager),
    ('ipyy', IPYYSMSManager),
    ('18sms', SYKJSMSManager),
    ('alidayu', ALIDAYUSMSManager),
)


def get_sms_manager_by_code(manager_code=None):
    if not manager_code:
        manager = SMSPlatform.objects.filter(is_default=True).first()
        if not manager:
            return None

        manager_code = manager.code

    return dict(SMS_CODE_MANAGER_TUPLE).get(manager_code)

