# -*- coding:utf-8 -*-
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import redirect
from flashsale.mmexam.models import Question, Result
from django.shortcuts import get_object_or_404, render
from flashsale.pay.options import get_user_unionid
import datetime
from django.shortcuts import render_to_response
from flashsale.xiaolumm.models import XiaoluMama


def index(request):
    START_QUESTION_NO = 61  # 考试开始题号
    content = request.GET
    code = content.get('code', None)
    user_openid, user_unionid = get_user_unionid(code,
                                                 appid=settings.WEIXIN_APPID,
                                                 secret=settings.WEIXIN_SECRET,
                                                 request=request)
    if not valid_openid(user_openid) or not valid_openid(user_unionid):
        redirect_url = "https://open.weixin.qq.com/connect/oauth2/authorize?appid=wxc2848fa1e1aa94b5&redirect_uri=http://m.xiaolumeimei.com/sale/exam/&response_type=code&scope=snsapi_base&state=135#wechat_redirect"
        return redirect(redirect_url)
    dt = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=36000),
                                    "%a, %d-%b-%Y %H:%M:%S GMT")
    data = {"start_question": START_QUESTION_NO}  # 设置开始题号
    response = render_to_response("mmexam/index.html", data, context_instance=RequestContext(request))
    response.set_cookie("unionid", user_unionid, expires=dt)
    return response


def exam(request, question_id):
    START_QUESTION_NO = 61  # 第二批考试题从34题开始
    END_QUESTION_NO = 86  # 结束试题号码
    if request.method == "POST":
        prequestion = get_object_or_404(Question, pk=question_id)  # 从数据库提取问题（question_id）
        if prequestion.single_many == 1:  # 如果是单选题
            answer = request.POST.get('choicebox', '')
        if prequestion.single_many == 2:  # 如果是多选题
            preanswer = request.POST.getlist('chk')
            answer = ''
            for m in range(len(preanswer)):  # 拼接字符串
                answer = answer + preanswer[m]  # 处理答案结果
        number = request.POST.get('number')
        rightanswer = prequestion.real_answer
        if answer != rightanswer:  # 答案不正确　返回提示
            return render(request, 'mmexam/mmexam_exam.html',
                          {'question': prequestion, 'result': "答案不正确，请参考培训资料，寻找正确答案", 'number': number})
        else:  # 回答正确
            try:
                question_id = int(question_id) + 1  # 考试题号加1
                if question_id == END_QUESTION_NO + 1:  # 如果回答的是最后一个问题　（这里设置　完成的题号）
                    user = request.COOKIES.get('unionid')
                    result, state = Result.objects.get_or_create(daili_user=user)
                    result.funish_Exam()
                    xlmm_id = get_object_or_404(XiaoluMama, openid=user).id
                    return render(request, 'mmexam/success_exam.html', {"xlmm": xlmm_id})
                else:  # 回答正确进入下一题
                    number = int(number) + 1  # 题号加１
                    question = get_object_or_404(Question, pk=question_id)
                    return render(request, 'mmexam/mmexam_exam.html',
                                  {'question': question, 'result': "", 'number': number})
            except:  # 出现异常
                question = get_object_or_404(Question, pk=START_QUESTION_NO)
                return render(request, 'mmexam/mmexam_exam.html',
                              {'result': "操作异常请重新开始考试", 'number': 1, 'question': question})
    else:
        if int(question_id) == START_QUESTION_NO:
            question = get_object_or_404(Question, pk=question_id)
            return render(request, 'mmexam/mmexam_exam.html',
                          {'question': question, 'result': "", 'number': 1})
        else:  # 如果题号不是开始题号则重定向从头开始
            return redirect("/sale/exam/")


import re

OPENID_RE = re.compile('^[a-zA-Z0-9-_]{28}$')


def valid_openid(openid):
    """ 合法有效 openid 正则匹配 """
    if not openid:
        return False
    if not OPENID_RE.match(openid):
        return False
    return True
