from core.weixin.options import gen_weixin_redirect_url

def in_weixin(request):
    user_agent = request.META.get('HTTP_USER_AGENT')
    if user_agent:
        user_agent = user_agent.lower()
        if user_agent.find('micromessenger') >= 0:
            return True
    return False
            

def check_sign(self, request):
    CONTENT = request.GET
    params  = {}
    for k,v in CONTENT.iteritems():
        params[k] = v
    timestamp = params.get('timestamp')
    if not timestamp or time.time() - int(timestamp) > 30:
        return False
    origin_sign = params.pop('sign')
    new_sign = options.gen_wxlogin_sha1_sign(params,settings.WXAPP_SECRET)
    if origin_sign and origin_sign == new_sign:
        return True
    params.update({'sign':origin_sign})
    logger.error('%s'%params)
    return False


class LoginViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    @list_route(methods=['post'])
    def customer_login(self, request):
        """验证用户登录"""
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next','/index.html')
        if not username or not password:
            return Response({"code":1, "result": u"用户名和密码不全呢！"})
     
        customers = Customer.objects.filter(mobile=username)
        if customers.count() == 1:
            # 若是微信授权创建的账户，django user的username不是手机号。
            username = customers[0].user.username
            
        user = authenticate(username=username, password=password)
        if not user or user.is_anonymous():
            return Response({"code": 2, "result": u"密码错误呢！"})  # 密码错误
        login(request, user)
        
        if in_weixin(request) and customers.count() == 1 and not customers[0].is_wxauth():
            params = {'appid':settings.WXPAY_APPID,
                      'redirect_uri':('{0}{1}?next={2}').format(settings.M_SITE_URL,reverse('v2:xlmm-wxauth'),next_url),
                      'response_type':'code',
                      'scope':'snsapi_base',
                      'state':'135'}
            next_url = gen_weixin_redirect_url(params)
            
        return Response({"code": 0, "result": "login", "next": next_url})


    @list_route(methods=['get'])
    def weixin_auth_and_redirect(self, request):
        next_url = request.REQUEST.get('next')
        code   = request.GET.get('code')
        
        if not in_weixin(request):
            return HttpResponseRedirect(next_url)
        
        user = request.user
        if not user or user.is_anonymous():
            return HttpResponseRedirect(next_url)
    
        if not code :
            params = {'appid':settings.WXPAY_APPID,
                      'redirect_uri':request.build_absolute_uri().split('#')[0],
                      'response_type':'code',
                      'scope':'snsapi_base',
                      'state':'135'}
            redirect_url = gen_weixin_redirect_url(params)
            
        return HttpResponseRedirect(redirect_url)
    
    
    @list_route(methods=['post'])
    def wxapp_login(self, request):
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
        if not check_sign(request):
            return Response({"code":1,"is_login":False, "info":"invalid sign"}) 
        
        params = request.POST
        user = authenticate(request=request,**params)
        if not user or user.is_anonymous():
            return Response({"code":2,"is_login":False, "info":"invalid user"})  
        login(request, user)
        
        customer = Customer.objects.get(user=request.user)
        serializer = serializers.CustomerSerializer(customer,context={'request': request})
        user_info  = serializer.data
        user_scores = Integral.objects.filter(integral_user=customer.id)
        user_score = 0
        if user_scores.count() > 0:
            user_score = user_scores[0].integral_value
        user_info['score'] = user_score
        
        return Response({"code":0,"is_login":True, "info":user_info})
