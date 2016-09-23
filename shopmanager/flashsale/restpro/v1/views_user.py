# -*- coding:utf-8 -*-
import os
import re
import urlparse
import time
import datetime
import decimal
import collections

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User as DjangoUser
from django.core.cache import cache

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework import renderers
from rest_framework import authentication
from rest_framework import exceptions

from core.options import log_action, ADDITION, CHANGE, get_systemoa_user
from core.weixin.options import gen_weixin_redirect_url
from core.weixin.options import gen_wxlogin_sha1_sign
from core.utils.httputils import get_client_ip

from flashsale.pay.models import Register, Customer, Integral, BudgetLog, UserBudget
from shopapp.smsmgr.tasks import task_register_code
from flashsale.restpro import permissions as perms
from . import serializers
import logging

logger = logging.getLogger(__name__)

PHONE_NUM_RE = re.compile(r'^0\d{2,3}\d{7,8}$|^1[34578]\d{9}$|^147\d{8}', re.IGNORECASE)
TIME_LIMIT = 360


def check_day_limit(reg_bean):
    if reg_bean.code_time and datetime.datetime.now().strftime('%Y-%m-%d') == reg_bean.code_time.strftime('%Y-%m-%d'):
        if reg_bean.verify_count >= 5:
            return True
        else:
            return False
    else:
        if reg_bean.verify_count >= 1:
            reg_bean.verify_count = 0
            reg_bean.save()
        return False


class RegisterViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    ## 特卖平台 用户注册,修改密码API：

    > ### /[.format]: `params={vmobile}` 注册新用户时，获取验证码;
    - 返回参数result：0-已经注册了;1-180秒不能重复发送;２－验证次数达上限;OK-表示获取成功;
    > ### /check_code_user: `params={username,valid_code}` 校验验证码（旧）;
    - 返回参数result：0-已经注册了;1-验证码过期或不对;２－参数格式不对;３-未获取验证码;7-注册成功;
    > ### /change_pwd_code: `params={vmobile}` 修改密码时，获取验证码api;
    - 返回参数result：0-验证码获取成功;1-尚无用户或者手机未绑定;２－当日验证次数超过上限;３-验证码过期;
    > ### /change_user_pwd: `params={username,valid_code,password1,password2}` 提交修改密码api;
    - 返回参数result：0-验证码获取成功;1-尚无用户或者手机未绑定;２－验证码不对;３-未获取验证码;４-验证码过期;５-校验异常;
    > ### /customer_login: `params={username,password}`　用户名，密码登陆
    - 返回参数code:0-登陆成功;1－参数不对；２－密码错误；３－用户未找到；4－账号异常；５-用户未设置密码；6－系统异常；
    > ### /wxapp_login: `params={headimgurl,nickname,openid,unionid}`　微信app授权登陆
    - 返回参数code:0-登陆成功;1－签名错误；２－非法用户；
    > ### /check_vcode: ｛mobile,vcode｝ ,校验验证码（新）;
    - 返回参数code：0-获取成功;1-验证码过期或超次;２－手机号码不合法;
    > ### /send_code: ｛mobile,｝ ,获取登录验证码;
    - 返回参数code：0-获取成功;1-验证码过期或超次;２－手机号码不合法;
    > ### /sms_login: ｛mobile,sms_code｝ ,通过验证码登录;
    - 返回参数code：0-获取成功;1-登录验证失败;２－手机号码不合法;3-验证码有误;
    """
    queryset = Register.objects.all()
    serializer_class = serializers.RegisterSerializer
    authentication_classes = ()
    permission_classes = ()
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_agent_src(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT')
        if not user_agent or user_agent.lower().find('windows') > 0:
            return 'windows'
        if user_agent.find('iphone') > 0:
            return 'iphone'
        if user_agent.find('android') > 0:
            return 'android'
        return user_agent

    def create(self, request, *args, **kwargs):
        """发送验证码时候新建register对象"""
        mobile = request.data.get('vmobile')
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if not mobile or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
            raise exceptions.APIException(u'手机号码格式不对')

        ip = get_client_ip(request)
        get_agent_src = self.get_agent_src(request)
        logger.debug('register: %s, %s, %s' % (ip, mobile, get_agent_src))

        if get_agent_src == 'windows':
            import random
            rnum = random.randint(1, 10)
            if rnum % 2 == 1:
                return Response({"result": "0", "code": 0, "info": "手机已注册"})
            else:
                return Response({"result": "OK", "code": 0, "info": "OK"})

        customers = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
        if customers.exists():
            return Response({"result": "0", "code": 0, "info": "手机已注册"})

        sysoa_user = get_systemoa_user()
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() > 0:
            temp_reg = reg[0]
            reg_pass = reg.filter(mobile_pass=True)
            if reg_pass.count() > 0:
                return Response({"result": "0", "code": 0, "info": "手机已注册"})  # 已经注册过
            if check_day_limit(temp_reg):
                return Response({"result": "2", "code": 2, "info": "当日验证次数超过5"})  # 当日验证次数超过5
            if temp_reg.code_time and temp_reg.code_time > last_send_time:
                return Response({"result": "1", "code": 1, "info": "180s内已经发送过"})  # 180s内已经发送过
            else:
                temp_reg.verify_code = temp_reg.genValidCode()
                temp_reg.code_time = current_time
                temp_reg.save()
                log_action(sysoa_user.id, temp_reg, CHANGE, u'修改，注册手机验证码')
                task_register_code.delay(mobile, "1")
                return Response({"result": "OK", "code": 0, "info": "OK"})
        else:
            try:
                new_reg = Register(vmobile=mobile)
                new_reg.verify_code = new_reg.genValidCode()
                new_reg.verify_count = 0
                new_reg.code_time = current_time
                new_reg.save()
            except IntegrityError:
                return Response({"result": "0", "code": 0, "info": "请勿重复点击"})
            log_action(sysoa_user.id, new_reg, ADDITION, u'新建，注册手机验证码')
            task_register_code.delay(mobile, "1")
            return Response({"result": "OK", "code": 0, "info": "OK"})

    def list(self, request, *args, **kwargs):
        return Response("not open")

    @list_route(methods=['post'])
    def check_code_user(self, request):
        """验证码校验（判断验证码是否过时，超次，并新建用户）"""
        post = request.REQUEST
        mobile = post['username']
        client_valid_code = post.get('valid_code', 0)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        reg = Register.objects.filter(vmobile=mobile)
        reg_pass = reg.filter(mobile_pass=True)
        already_exist = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
        if already_exist.count() > 0:
            return Response({"result": "0"})  # 已经有用户了
        if reg.count() == 0:
            return Response({"result": "3"})  # 未获取验证码
        elif reg_pass.count() > 0:
            return Response({"result": "0"})  # 已经注册过
        reg_temp = reg[0]
        server_verify_code = reg_temp.verify_code
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.save()
        if (reg_temp.code_time and reg_temp.code_time < last_send_time) or server_verify_code != client_valid_code:
            return Response({"result": "1"})  # 验证码过期或者不对
        form = UserCreationForm(post)
        if form.is_valid():
            new_user = form.save()
            a = Customer()
            a.user = new_user
            a.mobile = mobile
            a.save()
            reg_temp.mobile_pass = True
            reg_temp.cus_uid = a.id

            reg_temp.save()
            return Response({"result": "7"})  # 注册成功
        else:
            return Response({"result": "2"})  # 表单填写有误

    @list_route(methods=['post'])
    def change_pwd_code(self, request):
        """忘记密码时获取验证码"""
        mobile = request.data['vmobile']
        already_exist = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if already_exist.count() == 0:
            return Response({"result": "1"})  # 尚无用户或者手机未绑定
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断
            return Response({"result": "false"})

        sysoa_user = get_systemoa_user()
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.mobile_pass = True
            new_reg.code_time = current_time
            new_reg.save()
            log_action(sysoa_user.id, new_reg, ADDITION, u'新建，忘记密码验证码')
            task_register_code.delay(mobile, "2")
            return Response({"result": "0"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"result": "2"})  # 当日验证次数超过5
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"result": "3"})  # 180s内已经发送过
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(sysoa_user.id, reg_temp, CHANGE, u'修改，忘记密码验证码')
            task_register_code.delay(mobile, "2")
        return Response({"result": "0"})

    def is_login(self, request):
        if request.user and request.user.is_authenticated():
            return True
        return False

    @list_route(methods=['post'])
    def change_user_pwd(self, request):
        """手机校验修改密码"""
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)

        if not mobile or not passwd1 or not passwd2 or not verify_code or passwd2 != passwd1:
            return Response({"result": "2"})
        already_exist = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
        if not already_exist.exists():
            user = request.user
            if not user or user.is_anonymous():
                return Response({"result": "1"})  # 尚无用户或者手机未绑定
            already_exist = Customer.objects.filter(user=user).exclude(status=Customer.DELETE)
        customer = already_exist[0]
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"result": "3"})  # 未获取验证码
        reg_temp = reg[0]
        verify_code_server = reg_temp.verify_code
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.save()
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            return Response({"result": "4"})
        if verify_code_server != verify_code:
            return Response({"result": "3"})  # 验证码不对

        sysoa_user = get_systemoa_user()
        try:
            system_user = customer.user
            system_user.set_password(passwd1)
            system_user.save()
            reg_temp.cus_uid = already_exist[0].id
            reg_temp.save()
            if self.is_login(request):
                customer.mobile = mobile
                customer.save()
            log_action(sysoa_user.id, already_exist[0], CHANGE, u'忘记密码，修改成功')
            log_action(sysoa_user.id, reg_temp, CHANGE, u'忘记密码，修改成功')
        except:
            return Response({"result": "5"})
        return Response({"result": "0"})

    @list_route(methods=['post'])
    def check_vcode(self, request, **kwargs):
        """根据手机号和验证码创建用户账户"""
        content = request.REQUEST
        mobile = content.get('mobile')
        vcode = content.get('vcode')

        registers = Register.objects.filter(vmobile=mobile)
        if registers.count() == 0:
            return Response({'result': 2, 'error_msg': '未匹配到手机号'})

        register = registers[0]
        if not register.is_submitable() or not register.check_code(vcode):
            return Response({'result': 1,
                             'try_times': register.submit_count,
                             'limit_times': Register.MAX_SUBMIT_TIMES,
                             'error_msg': '手机验证失败'})

        customers = Customer.objects.filter(mobile=mobile, status=Customer.NORMAL)
        if customers.count() > 0:
            customer = customers[0]
        else:
            duser, state = DjangoUser.objects.get_or_create(username=mobile, is_active=True)
            customer, state = Customer.objects.get_or_create(user=duser)
            customer.mobile = mobile
            customer.save()
        return Response({'result': 0, 'mobile': mobile, 'valid_code': vcode, 'uid': customer.id})

    @list_route(methods=['post'])
    def customer_login(self, request):
        """验证用户登录"""
        # 获取用户名和密码
        # 判断网址的结尾是不是登录请求网址(ajax url请求)
        if not request.path.endswith("customer_login"):
            return Response({"result": "fail"})
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/index.html')
        if not username or not password:
            return Response({"code": 1, "result": "null"})
        try:
            try:
                customer = Customer.objects.get(mobile=username)
            except (Customer.DoesNotExist, Customer.MultipleObjectsReturned):
                pass
            else:
                username = customer.user.username

            user1 = authenticate(username=username, password=password)
            if not user1 or user1.is_anonymous():
                return Response({"code": 2, "result": "p_error"})  # 密码错误
            login(request, user1)

            user_agent = request.META.get('HTTP_USER_AGENT')
            if not user_agent or user_agent.find('MicroMessenger') < 0:
                return Response({"code": 0, "result": "login", "next": next_url})  # 登录不是来自微信，直接返回登录成功

            customers = Customer.objects.filter(user=user1).exclude(status=Customer.DELETE)
            if customers.count() == 0 or customers[0].is_wxauth():
                return Response({"code": 0, "result": "login", "next": next_url})  # 如果是系统帐号登录，或已经微信授权过，则直接返回登录成功

            params = {'appid': settings.WXPAY_APPID,
                      'redirect_uri': ('{0}{1}?next={2}').format(settings.M_SITE_URL, reverse('rest_v1:xlmm-wxauth'),
                                                                 next_url),
                      'response_type': 'code',
                      'scope': 'snsapi_base',
                      'state': '135'}
            redirect_url = gen_weixin_redirect_url(params)
            return Response({"code": 0, "result": "login", "next": redirect_url})  # 如果用户没有微信授权则直接微信授权后跳转

        except Customer.DoesNotExist:
            return Response({"code": 3, "result": "u_error"})  # # 用户错误
        except Customer.MultipleObjectsReturned:
            return Response({"code": 4, "result": "s_error"})  # 账户异常
        except ValueError, exc:
            return Response({"code": 5, "result": "no_pwd"})
        return Response({"code": 6, "result": "fail"})

    def check_sign(self, request):
        CONTENT = request.GET
        params = {}
        for k, v in CONTENT.iteritems():
            params[k] = v
        timestamp = params.get('timestamp')
        if not timestamp or time.time() - int(timestamp) > 6 * 60 * 60:
            logger.error('wxapp sign timeout: %s' % params)
            return False
        origin_sign = params.pop('sign')
        new_sign = gen_wxlogin_sha1_sign(params, settings.WXAPP_SECRET)
        if origin_sign and origin_sign == new_sign:
            return True
        params.update({'sign': origin_sign})
        logger.error('%s' % params)
        return False

    @list_route(methods=['get', 'post'])
    def wxapp_login(self, request, *args, **kwargs):
        """微信app 登录接口数据校验算法:
            　参数：params = {'a':1,'c':2,'b':3}
            时间戳：timestamp = 1442995986
         随机字符串：noncestr = 8位随机字符串，如abcdef45
        　 　secret : 3c7b4e3eb5ae4c (测试值)
           签名步骤:
           1，获得所有签名参数：
           　sign_params = {timestamp:时间戳,noncestr:随机值,secret:密钥值}
           如　{'timestamp':'1442995986','noncestr':'1442995986abcdef','secret':'3c7b4e3eb5ae4c'}
           2,根据参数的字符串key，进行升序排列,并组装成新的字符串，如：
            sign_string = '&'.join(sort([k=v for k,v in sign_params],asc=true))
           如　'noncestr=1442995986abcdef&secret=3c7b4e3eb5ae4c&timestamp=1442995986'
           3,签名算法
            sign = hash.sha1(sign_string).hexdigest()
            如　签名值＝'39ae931c59394c9b4b0973b3902956f63a35c21e'
           4,最后传递给服务器的参数：
           URL:~?noncestr=1442995986abcdef&timestamp=1442995986&sign=366a83819b064149a7f4e9f6c06f1e60eaeb02f7
           POST: 'a=1&b=3&c=2'
        """
        if not self.check_sign(request):
            return Response({"code": 1, "is_login": False, "info": "invalid sign"})

        req_params = request.POST
        user1 = authenticate(request=request, **req_params)
        if not user1 or user1.is_anonymous():
            return Response({"code": 2, "is_login": False, "info": "invalid user"})
        login(request, user1)

        customer = get_object_or_404(Customer, user=request.user)
        serializer = serializers.CustomerSerializer(customer, context={'request': request})
        user_info = serializer.data
        user_scores = Integral.objects.filter(integral_user=customer.id)
        user_score = 0
        if user_scores.count() > 0:
            user_score = user_scores[0].integral_value
        user_info['score'] = user_score

        return Response({"code": 0, "is_login": True, "info": user_info})

    @list_route(methods=['post'])
    def send_code(self, request, *args, **kwargs):
        """ 根据手机号获取验证码 """
        mobile = request.REQUEST['mobile']
        current_time = datetime.datetime.now()
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):
            return Response({"code": 2, "info": "手机号码有误"})
        new_reg, state = Register.objects.get_or_create(vmobile=mobile)
        if not new_reg.is_verifyable():
            return Response({"code": 1, "info": "获取验证码失败"})
        new_reg.verify_code = new_reg.genValidCode()
        new_reg.verify_count = 1
        new_reg.code_time = current_time
        new_reg.save()
        task_register_code.delay(mobile, "1")
        return Response({"code": 0, "info": "验证码已发送"})

    @list_route(methods=['post'])
    def sms_login(self, request, *args, **kwargs):
        """ 短信验证码登陆 """
        req_params = request.REQUEST
        mobile = req_params.get('mobile', '')
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):
            return Response({"code": 2, "info": "手机号码有误"})
        sms_code = req_params.get('sms_code', '')
        if not sms_code or not sms_code.isdigit():
            return Response({"code": 3, "info": "验证码有误"})

        user1 = authenticate(request=request, **req_params)
        if not user1 or user1.is_anonymous():
            return Response({"code": 1, "info": "登录验证失败"})
        login(request, user1)

        customer = get_object_or_404(Customer, user=request.user)
        serializer = serializers.CustomerSerializer(customer, context={'request': request})
        user_info = serializer.data
        user_scores = Integral.objects.filter(integral_user=customer.id)
        user_score = 0
        if user_scores.count() > 0:
            user_score = user_scores[0].integral_value
        user_info['score'] = user_score

        return Response({"code": 0, "info": user_info})


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ## 特卖平台 用户操作API：
    > ###　/profile: 获取用户信息;
    > ###　/islogin: 判断用户是否登陆;
    -code:0　表示已登陆，返回http:403,错误表示登陆失效
    > ###/need_set_info: 获取该用户是否需要设置密码;
    - code: 0,不需要设置密码;1: 已经有手机，需要设置密码;2:需要设置密码，并且需要绑定手机;
    > ### /customer_logout: 用户注销api;
    - code: 0,退出成功；
    > ### /bang_mobile_code: `params={vmobile}`绑定手机时候获取验证码;
    - code: 0,发送成功；1,手机号码已注册；２，当日验证超过５次；３，180s已发过验证码；４，手机号码不对；
    > ### /bang_mobile: `params={username, password1, password2, valid_code}`绑定手机;
    - code: 0,绑定成功；1,手机已经绑定;2,手机号码不对;3,验证码不对;4,验证码过期;5,系统异常;
    > ### /passwd_set: `params={password1, password2}`初始化密码;
    - code: 0,设置成功；1,密码格式不对;
    > ### /change_pwd_code: 修改密码时获取验证码;
    - code: 0,发送成功；1,手机号码不对;2,当日验证次数超过5;3,180s内已经发送过;
    > ### /change_user_pwd: `params={username, password1, password2}`提交修改密码;
    - code: 0,修改成功；2,手机密码格式不对;3,验证码不对;4,验证码过期;5,系统异常;
    > ### /check_code: `params={username, valid_code}`验证码判断、验证码过时功能;
    - code: 0,验证通过；1,已经绑定用户;2,手机验证码不对;3,手机未注册;4,验证码过期;5,验证码不对;
    """
    queryset = Customer.objects.all()
    serializer_class = serializers.CustomerSerializer
    #authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated, perms.IsOwnerOnly)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    def get_owner_queryset(self, request):
        if request.user.is_anonymous():
            return self.queryset.none()
        return self.queryset.filter(user=request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_owner_queryset(request))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'])
    def profile(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, user=request.user)
        # TODO@meron need invalidate?
        profile_key = 'cusotmer-profile-key-{0}'.format(customer.id)
        user_info = cache.get(profile_key)
        if not user_info:
            user_info = self.get_serializer(customer).data
            cache.set(profile_key, user_info, 10)

        return Response(user_info)

    def perform_destroy(self, instance):
        instance.status = Customer.DELETE
        instance.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'code':0, 'info':u'保存成功'})

    @list_route(methods=['get', 'post'])
    def customer_logout(self, request, *args, **kwargs):
        logout(request)
        return Response({"code": 0, "result": 'logout'})

    @list_route(methods=['get'])
    def islogin(self, request, *args, **kwargs):
        return Response({"code": 0, 'result': 'login'})

    @list_route(methods=['get'])
    def need_set_info(self, request):
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        has_set_passwd = True
        # try:
        #     user = customer.user
        #     # authenticate(username=user.username, password=u"testxiaolummpasswd")
        #     # authenticate(username="testxiaolu", password=u"testxiaolummpasswd")
        # except ValueError, exc:
        #     # has_set_passwd = False

        if customer.mobile and len(customer.mobile) == 11:
            if has_set_passwd:
                return Response({'code': 0, 'result': 'no', 'mobile': customer.mobile, 'info': ''})
            else:
                return Response({'code': 1, 'result': '1', 'mobile': customer.mobile, 'info': '没有设置密码'})
        else:
            return Response({'code': 2, 'result': 'yes', 'info': '没有设置手机号'})

    @list_route(methods=['post'])
    def bang_mobile_code(self, request):
        """绑定手机时获取验证码"""
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if len(customer.mobile) != 0:
            raise exceptions.APIException(u'账户异常，请联系客服～')
        mobile = request.data['vmobile']
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):
            return Response({"code": 4, "result": "false", "info": "请输入正确的手机号"})
        already_exist = Customer.objects.filter(mobile=mobile).exclude(user__username=mobile)
        if already_exist.count() > 0:
            return Response({"code": 1, "result": "1", "info": "手机已经绑定"})

        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.code_time = current_time
            new_reg.save()
            log_action(request.user.id, new_reg, ADDITION, u'新建，绑定手机验证码')
            task_register_code.delay(mobile, "3")
            return Response({"code": 0, "result": "0", "info": "发送成功"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"code": 2, "result": "2", "info": "当日验证次数超过5"})
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"code": 3, "result": "3", "info": "180s内已经发送过"})
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(request.user.id, reg_temp, CHANGE, u'绑定手机获取验证码')
            task_register_code.delay(mobile, "3")
        return Response({"code": 0, "result": "0", "info": "发送成功"})

    @list_route(methods=['post'])
    def bang_mobile(self, request):
        """绑定手机,并初始化密码"""
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if not mobile or not passwd1 or not passwd2 or not verify_code or len(mobile) == 0 \
                or len(passwd1) == 0 or len(verify_code) == 0 or passwd2 != passwd1:
            return Response({"code": 2, "info": "手机号密码不对", "result": "2"})
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断，待写
            return Response({"code": 2, "info": "手机号码不对", "result": "2"})
        # 用户避免用户手机号绑定多个微信账号
        already_exist = Customer.objects.filter(mobile=mobile).exclude(user__username=mobile)
        if already_exist.count() > 0:
            return Response({"code": 1, "info": "手机已经绑定", "result": "1"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if len(customer.mobile) != 0:
            raise exceptions.APIException(u'账户异常，请联系客服～')
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"code": 3, "info": "验证码不对", "result": "3"})
        reg_temp = reg[0]
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.save()
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码过期')
            return Response({"code": 4, "info": "验证码过期", "result": "4"})
        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码不对')
            return Response({"code": 3, "info": "验证码不对", "result": "3"})
        try:
            customer.mobile = mobile
            customer.save()
            log_action(request.user.id, customer, CHANGE, u'手机绑定成功')
            reg_temp.cus_uid = customer.id
            reg_temp.mobile_pass = True
            reg_temp.save()
            log_action(request.user.id, reg_temp, CHANGE, u'手机绑定成功')
            system_user = customer.user
            system_user.set_password(passwd1)
            system_user.save()
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
            return Response({"code": 5, "result": "5", 'info': exc.message})
        return Response({"code": 0, "result": "0", 'info': 'success'})

    @list_route(methods=['post'])
    def bang_mobile_unpassword(self, request):
        """绑定手机,并初始化密码"""
        mobile = request.data['username']
        verify_code = request.data['valid_code']
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        if not mobile or not verify_code or len(mobile) == 0 or len(verify_code) == 0:
            return Response({"code": 2, "info": "手机号密码不对", "result": "2"})
        if mobile == "" or not re.match(PHONE_NUM_RE, mobile):  # 进行正则判断，待写
            return Response({"code": 2, "info": "手机号码不对", "result": "2"})
        already_exist = Customer.objects.filter(mobile=mobile).exclude(user__username=mobile)
        if already_exist.count() > 0:
            return Response({"code": 1, "info": "手机已经绑定", "result": "1"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if len(customer.mobile) != 0:
            raise exceptions.APIException(u'账户异常，请联系客服～')
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"code": 3, "info": "验证码不对", "result": "3"})
        reg_temp = reg[0]
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.save()
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码过期')
            return Response({"code": 4, "info": "验证码过期", "result": "4"})
        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            log_action(request.user.id, reg_temp, CHANGE, u'验证码不对')
            return Response({"code": 3, "info": "验证码不对", "result": "3"})
        try:
            customer.mobile = mobile
            customer.save()
            log_action(request.user.id, customer, CHANGE, u'手机绑定成功')
            reg_temp.cus_uid = customer.id
            reg_temp.mobile_pass = True
            reg_temp.save()
            log_action(request.user.id, reg_temp, CHANGE, u'手机绑定成功')
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
            return Response({"code": 5, "result": "5", 'info': exc.message})
        return Response({"code": 0, "result": "0", 'info': 'success'})

    @list_route(methods=['post'])
    def passwd_set(self, request):
        """初始化密码"""
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        if not passwd1 and not passwd2 and len(passwd1) < 6 and len(passwd2) < 6 and passwd2 != passwd1:
            return Response({"code": 1, "result": "1", "info": "密码格式不对"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        log_action(request.user.id, customer, CHANGE, u'第一次设置密码成功')
        django_user.set_password(passwd1)
        django_user.save()
        register_qs = Register.objects.filter(vmobile=customer.mobile)
        if register_qs.count() == 0:
            new_register = Register(vmobile=customer.mobile, cus_uid=customer.id, initialize_pwd=True, mobile_pass=True)
            new_register.verify_code = new_register.genValidCode()
            new_register.save()
            log_action(request.user.id, new_register, ADDITION, u'初始化密码')
        else:
            temp_register = register_qs[0]
            temp_register.initialize_pwd = True
            temp_register.mobile_pass = True
            temp_register.verify_code = temp_register.genValidCode()
            temp_register.save()
            log_action(request.user.id, temp_register, CHANGE, u'已有，初始化密码')
        return Response({"code": 0, "result": "0", "info": "success"})

    @list_route(methods=['post'])
    def change_pwd_code(self, request):
        """修改密码时获取验证码"""
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if customer.mobile == "" or not re.match(PHONE_NUM_RE, customer.mobile):  # 进行正则判断，待写
            return Response({"code": 1, "result": "false", "info": "手机号码不对"})
        reg = Register.objects.filter(vmobile=customer.mobile)
        if reg.count() == 0:
            new_reg = Register(vmobile=customer.mobile)
            new_reg.verify_code = new_reg.genValidCode()
            new_reg.verify_count = 0
            new_reg.mobile_pass = True
            new_reg.code_time = current_time
            new_reg.save()
            log_action(request.user.id, new_reg, ADDITION, u'登录后，新建，修改密码')
            task_register_code.delay(customer.mobile, "2")
            return Response({"code": 0, "result": "0", "info": "success"})
        else:
            reg_temp = reg[0]
            if check_day_limit(reg_temp):
                return Response({"code": 2, "result": "2", "info": "当日验证次数超过5"})
            if reg_temp.code_time and reg_temp.code_time > last_send_time:
                return Response({"code": 3, "result": "3", "info": "180s内已经发送过"})
            reg_temp.verify_code = reg_temp.genValidCode()
            reg_temp.code_time = current_time
            reg_temp.save()
            log_action(request.user.id, reg_temp, ADDITION, u'登录后，修改密码')
            task_register_code.delay(customer.mobile, "2")
        return Response({"code": 0, "result": "0", "info": "success"})

    @list_route(methods=['post'])
    def change_user_pwd(self, request):
        """提交修改密码"""
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        mobile = request.data['username']
        passwd1 = request.data['password1']
        passwd2 = request.data['password2']
        verify_code = request.data['valid_code']

        if not mobile or not passwd1 or not passwd2 or not verify_code or len(mobile) == 0 \
                or len(passwd1) == 0 or len(verify_code) == 0 or passwd2 != passwd1:
            return Response({"code": 2, "result": "2", "info": "手机密码格式不对"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        if customer.mobile != mobile:
            raise exceptions.APIException(u'用户信息异常')
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"code": 3, "result": "3", "info": "验证码不对"})
        reg_temp = reg[0]
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.cus_uid = customer.id
        reg_temp.save()
        log_action(request.user.id, reg_temp, CHANGE, u'修改密码')
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            return Response({"code": 4, "result": "4", "info": "验证码过期"})

        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            return Response({"code": 3, "result": "3", "info": "验证码不对"})
        try:
            system_user = customer.user
            system_user.set_password(passwd1)
            system_user.save()
            log_action(request.user.id, customer, CHANGE, u'修改密码')
        except Exception, exc:
            logger.error(exc.message or 'empty error', exc_info=True)
            return Response({"code": 5, "result": "5", "info": "系统异常"})
        return Response({"code": 0, "result": "0", "info": "success"})

    @list_route(methods=['post'])
    def check_code(self, request):
        """验证码判断、验证码过时功能"""
        current_time = datetime.datetime.now()
        last_send_time = current_time - datetime.timedelta(seconds=TIME_LIMIT)
        mobile = request.data['username']
        verify_code = request.data['valid_code']

        if not mobile or not verify_code or len(mobile) == 0 or len(verify_code) == 0:
            return Response({"code": 2, "result": "2", "info": "手机验证码不对"})
        already_exist = Customer.objects.filter(mobile=mobile).exclude(status=Customer.DELETE)
        if already_exist.count() > 0:
            return Response({"code": 1, "result": "1", "info": "已经绑定用户"})
        django_user = request.user
        customer = get_object_or_404(Customer, user=django_user)
        reg = Register.objects.filter(vmobile=mobile)
        if reg.count() == 0:
            return Response({"code": 3, "result": "3", "info": "手机未注册"})
        reg_temp = reg[0]
        reg_temp.submit_count += 1  # 提交次数加一
        reg_temp.cus_uid = customer.id
        reg_temp.save()
        log_action(request.user.id, reg_temp, CHANGE, u'验证码验证')
        if reg_temp.code_time and reg_temp.code_time < last_send_time:
            return Response({"code": 4, "result": "4", "info": "验证码过期"})

        verify_code_server = reg_temp.verify_code
        if verify_code_server != verify_code:
            return Response({"code": 5, "result": "5", "info": "验证码不对"})
        return Response({"code": 0, "result": "OK", "info": "success"})

    @list_route(methods=['get'])
    def get_budget_detail(self, request):
        """ 特卖用户钱包明细记录"""
        customer = get_object_or_404(Customer, user=request.user)
        budget_logs = BudgetLog.objects.filter(
            customer_id=customer.id).exclude(
            status=BudgetLog.CANCELED).order_by('-created')
        page = self.paginate_queryset(budget_logs)
        if page is not None:
            serializer = serializers.BudgetLogSerialize(page,
                                                        many=True,
                                                        context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.BudgetLogSerialize(budget_logs, many=True)
        return Response(serializer.data)

    @list_route(methods=['get, post'])
    def cash_out_once(self, request):
        """
        第一次从web界面提现，只允许一次，建立客户信任。
        POST /rest/v1/users/cash_out_once
        """
        customer = get_object_or_404(Customer, user=request.user)
        customer_id = customer.id

        count = BudgetLog.objects.filter(customer_id=customer_id, budget_type=BudgetLog.BUDGET_OUT, budget_log_type=BudgetLog.BG_CASHOUT).exclude(status=BudgetLog.CANCELED).count()
        if count > 0:
            return Response({"code": 1, "message": u"由于微信的提现请求繁忙，网页提现限首次使用，下载APP登录即可多次提现！"})

        return self.budget_cash_out(request)
        
    
    @list_route(methods=['post'])
    def budget_cash_out(self, request):
        """
        小鹿钱包提现接口

        POST /rest/v1/users/budget_cash_out
        参数：
        - cashout_amount  必填，提现金额（单位：元）
        - channel  选填，可选项（wx：提现请求来源于微信公众号）

        返回：
        {'code': xx, 'message': xxx, 'qrcode': xxx}
        - 返回`code`:
            0 成功;
            1　提现金额小于0;
            2 提现金额大于当前账户金额;
            3 参数错误;
            4　用户没有公众号账号;
            5　用户unionid不存在
            6 提现不能超过200
           11　已经提现过一次无审核２元
        """
        content = request.POST
        cashout_amount = content.get('cashout_amount', None)
        channel = content.get('channel', None)
        verify_code = content.get('verify_code', None)
        default_return = collections.defaultdict(code=0, message='', qrcode='')

        if not cashout_amount:
            return Response({'code': 3, 'message': '参数错误', 'qrcode': ''})

        customer = get_object_or_404(Customer, user=request.user)
        if not customer.status == Customer.NORMAL:
            info = u'你的帐号已被冻结，请联系管理员！'
            return Response({"code": 10, "info": info}) 

        budget = get_object_or_404(UserBudget, user=customer)
        amount = int(decimal.Decimal(cashout_amount) * 100)  # 以分为单位(提现金额乘以100取整)

        code, info = budget.action_budget_cashout(amount, verify_code=verify_code)
        qrcode = ''
        return Response({'code': code, "message": info, "info": info, "qrcode": qrcode})

    @list_route(methods=['get'])
    def get_wxpub_authinfo(self, request):
        """
        提示用户关注公众账号接口
        """
        customer = get_object_or_404(Customer, user=request.user)
        # 这里的公众账号　访问地址要带上用户的信息　例如customer
        return Response({'auth_link': urlparse.urljoin(settings.M_SITE_URL,
                                                       reverse('rest_v1:user-budget-bang', kwargs={'pk': customer.id})),
                         'auth_msg': '将图片二维码图片保存本地后，打开微信扫一扫从相册选取二维码图片'})

    @list_route(methods=['post'])
    def open_debug_for_app(self, request):
        content = request.REQUEST
        debug_secret = content.get("debug_secret") or ''
        if debug_secret != "xlmm@16888&a":
            return Response({"rcode": 1, "msg": "开启失败"})
        return Response({"rcode": 0, "msg": "开启成功"})

from django.shortcuts import redirect
from django.contrib.auth.models import User
from rest_framework.views import APIView
from core.weixin.mixins import WeixinAuthMixin
from flashsale.pay.tasks import task_Refresh_Sale_Customer


class UserBugetBangView(WeixinAuthMixin, APIView):
    """ 特卖用户钱包View """
    #     serializer_class = serializers.ProductSerializer
    authentication_classes = ()
    permission_classes = ()
    renderer_classes = (renderers.JSONRenderer, renderers.TemplateHTMLRenderer)
    template_name = 'user_budget_bang.html'

    def get(self, request, pk, format=None, *args, **kwargs):

        self.set_appid_and_secret(settings.WXPAY_APPID, settings.WXPAY_SECRET)
        user_infos = self.get_auth_userinfo(request)
        unionid = user_infos.get('unionid')
        openid = user_infos.get('openid')
        if not self.valid_openid(unionid):
            redirect_url = self.get_snsuserinfo_redirct_url(request)
            return redirect(redirect_url)
        user_infos.update(
            {'headimgurl': user_infos.get('headimgurl') or 'http://7xogkj.com2.z0.glb.qiniucdn.com/222-ohmydeer.png',
             'nick': user_infos.get('nick') or '没有昵称'
             })
        customers = Customer.objects.filter(unionid=unionid, status=Customer.NORMAL)
        response = None
        if not customers.exists():
            customer = get_object_or_404(Customer, pk=pk)
            cus_unionid = customer.unionid
            if cus_unionid.strip() and cus_unionid != unionid:
                response = Response({'code': 2, 'info': '您的提现账号已绑定小鹿美美公众号', 'user_infos': user_infos})
        else:
            customer = customers[0]
            if customer.pk != pk:
                response = Response({'code': 1, 'info': '当前授权微信号已绑定其它提现账号，请更换微信号重试～', 'user_infos': user_infos})

        if not response:
            customer.unionid = unionid
            customer.save()

            task_Refresh_Sale_Customer.delay(user_infos, app_key=self._wxpubid)
            response = Response({'code': 0, 'info': '恭喜，您成功绑定小鹿美美提众号！', 'user_infos': user_infos})

        self.set_cookie_openid_and_unionid(response, openid, unionid)
        return response
