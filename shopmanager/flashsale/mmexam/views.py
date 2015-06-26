#-*- coding:utf-8 -*-
import time
import json
import random
from django.conf import settings
from django.http import HttpResponse,HttpResponseRedirect  
from django.template import RequestContext 
from django.shortcuts import render,redirect
from django.views.decorators.csrf import csrf_exempt
from flashsale.mmexam.models import Question,Choice,Result
from django.shortcuts import get_object_or_404, render
from flashsale.pay.options import get_user_unionid
import datetime

def index(request):
    
    #这里得到openid
   # print "这里是首页"
    content = request.REQUEST
    code = content.get('code',None)
    user_openid,user_unionid = get_user_unionid(code,
                                                appid=settings.WEIXIN_APPID,
                                                secret=settings.WEIXIN_SECRET,
                                                request=request)
        
    if not valid_openid(user_openid) or not valid_openid(user_unionid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://weixin.huyi.so/sale/exam/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
        return redirect(redirect_url)
    #    if not user_openid  or user_openid.upper() == 'NONE':
            #render(request, 'invalid_user.html')#无效用户
   
    dt = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=36000), "%a, %d-%b-%Y %H:%M:%S GMT")
    response=render(request, 'index.html')
    #response.set_cookie("openid", "多选测试")
    
   # print "这里是 zuixin"
    response.set_cookie("unionid", user_unionid, expires=dt)
    return response

def exam(request,question_id):
    
    if request.method == "POST":
        prequestion = get_object_or_404(Question, pk=question_id)
        if prequestion.single_many==1:
            answer=request.POST.get('choicebox','')
        if prequestion.single_many==2:
            preanswer=request.POST.getlist('chk')
            answer=''
            for m in range(len(preanswer)):#拼接字符串
                print preanswer[m]
                answer=answer+preanswer[m]
            print "拼接结果",answer
        print "答案",answer
        number=request.POST.get('number')
        print "答题数目",answer
        #prequestion = get_object_or_404(Question, pk=question_id)
        rightanswer = prequestion.real_answer
        print "答案",rightanswer
        if answer!=rightanswer:
            #question = get_object_or_404(Question, pk=question_id)
#             print "正确问题是",question.id,question.question
            #return render(request, 'mmexam_exam.html', {'question_id': question_id})
            return render(request, 'mmexam_exam.html', {'question': prequestion,'result':"答案不正确，请参考培训资料，寻找正确答案",'number':number})
        else:
            try:
                question_id = int(question_id)+1
                print '下一题',question_id
                #print '答题数目为',number
                if question_id == 61:
                    user = request.COOKIES.get('unionid')
                    result, state = Result.objects.get_or_create(daili_user=user)
                    result.funish_Exam()
                    return render(request, 'success_exam.html')
                else:
                    number = int(number)+1 #这时候number+1
                    question_num = question_id - 33
                    question2 = Question.objects.get(pk=question_id)
                    question = get_object_or_404(Question, pk=question_id)
                    print question_num,"eeeeeeeeeeeeeeee"
                    return render(request, 'mmexam_exam.html', {'question': question,'result':"",'number':number,
                                                                'question_num': question_num})

            except:
                user=request.COOKIES.get('unionid')
                print "openid",user
                #Result.objects.create(daili_user="方",exam_state=1)  #这里对结果统一赋值
                result, state = Result.objects.get_or_create(daili_user=user)
                result.funish_Exam()
                return render(request, 'success_exam.html')
             
    
    else :
        #try:
            #question = Question.objects.get(pk=question_id)
            #question = get_object_or_404(Question, pk=question_id)
            #return render(request, 'mmexam_exam.html', {'question': question})
        #except():
        print "初始id",question_id
        if int(question_id) == 34:
            question = get_object_or_404(Question, pk=question_id)
#         number=0
            print "选题类型",question.single_many
            return render(request, 'mmexam_exam.html', {'question': question,'result':"",'number':1,'question_num': 1})
        else:
           # return  render(request, 'index.html')   
           return redirect("/sale/exam/")
    #question_id = int(question_id)+1
    #question = get_object_or_404(Question, pk=question_id)
    #print "问题是",question.id,question.question
    #return render(request, 'mmexam_exam.html', {'question': question})
import re
OPENID_RE = re.compile('^[a-zA-Z0-9-_]{28}$')
def valid_openid(openid):
    if not openid:
        return False
    if not OPENID_RE.match(openid):
        return False
    return True 
#图片


