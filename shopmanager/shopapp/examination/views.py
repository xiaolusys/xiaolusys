#-*- coding:utf-8 -*-
import time
import json
import random
from django.http import HttpResponse
from django.template import RequestContext 
from django.shortcuts import render_to_response
from shopapp.examination.models import ExamProblemSelect,ExamUser,ExamPaper
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
#from django.contrib.admin.views.decorators import staff_member_required
import logging

logger = logging.getLogger('django.request')

#@staff_member_required
@csrf_exempt
def examination_user(request):
#    进入页面，得到用户及考试信息，rander到页面
    content=request.GET
    user = request.user
#    第一步，拿到paperID（卷），p_id(题号)
#####################################################################
#   统计已生成考卷数
    paper_count = ExamPaper.objects.filter(user=user)
    paper_id_array = []
    for c in paper_count:
        paper_id_array.append(c.paper_id)
    paper_id_array_acount = len(set(paper_id_array))
    print 'set(paper_id_array)',paper_id_array_acount
    if (paper_id_array_acount>2):
        return render_to_response('examination/exam_end.html',{"A":2, },context_instance=RequestContext(request)) 
#####################################################################
#    卷
    paper_id = content.get('paper_id')
    if (paper_id==None):
#    生成具体时间
        t = time.time()
        timeArray = time.localtime(t)
        otherStyleTime = time.strftime("%Y%m%d%H%M%S", timeArray)
#    paperID是userID+年月日时分秒，来保证唯一
        paper_id = str(user)+otherStyleTime
    else:
        ExamPaper.objects.filter(paper_id=paper_id).delete()
#####################################################################
#    第二步，生成paper考题数量,再判断是否超出题库
    problem_count = content.get('problem_count')
    if (problem_count==None):
        problem_count = 3
    else:
        problem_count = str(problem_count)
        try:
            problem_count = int(problem_count)
        except:
            pass
#####################################################################
# 更改“设定题目数量”选项的最大长度，及输出提示
    p_list = []
    text = ''
    problem = ExamProblemSelect.objects.all()
#   生成p.id list
    for p in problem:
        p_list.append(p.id)
    if (problem_count>len(p_list)):
        problem_count = len(p_list)
        text = '最大长度为'+str(len(p_list))
    problem_l = random.sample(p_list,problem_count)
#####################################################################           
#   这里还要有一个生成problem_list前期写入数据库的方法
    try:
        write_paper_l(user,problem_l,paper_id)
    except:
        pass
    problem_len = len(ExamProblemSelect.objects.all())
#####################################################################
#   统计已生成考卷数
#    paper_count = ExamPaper.objects.filter(user=user)
#    paper_id_array = []
#    for c in paper_count:
#        paper_id_array.append(c.paper_id)
#    paper_id_array_acount = len(set(paper_id_array))
#    print 'set(paper_id_array)',paper_id_array_acount
#####################################################################
    
    return render_to_response('examination/exam_index.html',{'paper_id':paper_id,
                                                             'user':user,
                                                             'problem_count':problem_count,
                                                             'text':text,
                                                             'problem_len':problem_len,
                                                             },context_instance=RequestContext(request))
                                              
#problem_l 预存到数据库
def write_paper_l(user,problem_l,paper_id):
    user = user
    problem_l = problem_l
    paper_id = paper_id
    for k in problem_l:
        problem_id = k
        problem = ExamProblemSelect.objects.get(id=k)
        exam_answer = problem.exam_answer
        exam_problem_score = problem.exam_problem_score
        e_exam_selected,state = ExamPaper.objects.get_or_create(problem_id=problem_id,
                                                                exam_answer=exam_answer,
                                                                paper_id=paper_id,
                                                                user=user,)
        e_exam_selected.exam_problem_score = exam_problem_score
        e_exam_selected.save()
    
    return  HttpResponse(json.dumps({'response_content':'success'}),mimetype="application/json")


#开始考试
#@staff_member_required
@csrf_exempt    
def start_exam(request):
    content=request.GET
    user   = request.user
    paper_id        = content.get('paper_id')
    problem_count   = content.get('problem_count')
    problem_count_u = content.get('problem_count')
    problem_count = str(problem_count)
    problem_count = int(problem_count)
    p_id = content.get('p_id')
#    或者problem_count在判断和p_id的关系，而不是抛出错误
    try:
        if (p_id==''):
            p_id = 1
        elif (p_id==problem_count_u):
            p_id=str(p_id)
            p_id=int(p_id)
            grade_total = exam_grade(paper_id,user)
            return render_to_response('examination/exam_finish.html',{'user':user,'paper_id':paper_id,
                                                                      'problem_count':problem_count,
                                                                      'grade_total':grade_total
                                                                      },context_instance=RequestContext(request))
        else:
            p_id=str(p_id)
            p_id=int(p_id)
            p_id=p_id+1
        problem_paper = ExamPaper.objects.filter(paper_id=paper_id)
        problem_id = problem_paper[p_id-1].problem_id
        problem = ExamProblemSelect.objects.get(id=problem_id)
        return render_to_response('examination/exam_admin.html',{'paper_id':paper_id,
                                                                 'user':user,
                                                                 'problem_paper':problem_paper,
                                                                 'problem':problem,
                                                                 'p_id':p_id,
                                                                 'problem_count':problem_count
                                                                 },context_instance=RequestContext(request))
    except Exception,exc:
        logger.error(exc.message or str(exc),exc_info=True)
        grade_total = exam_grade(paper_id,user)
        return render_to_response('examination/exam_finish.html',{'user':user,
                                                                  'paper_id':paper_id,
                                                                  'problem_count':problem_count,
                                                                  'grade_total':grade_total
                                                                  },context_instance=RequestContext(request))
                                                   
#@staff_member_required                    
@csrf_exempt     
def write_select_paper(request):
    content=request.GET
    id = content.get('id')
    paper_id = content.get('paper_id')
    exam_selected = content.get('exam_selected')
    problem       = ExamProblemSelect.objects.get(id=id)
    problem_id    = problem.id
    exam_selected = exam_selected
    exam_answer   = problem.exam_answer
    
    e_exam_selected,state = ExamPaper.objects.get_or_create(problem_id=problem_id,paper_id=paper_id,)
    
    e_exam_selected.user = request.user
    e_exam_selected.paper_id = paper_id
    e_exam_selected.exam_answer = exam_answer
    e_exam_selected.exam_selected = exam_selected
    
    if (exam_selected == 'A'):
        e_exam_selected.exam_selected = ExamPaper.SELECTED_A
    elif(exam_selected == 'B'):
        e_exam_selected.exam_selected = ExamPaper.SELECTED_B
    elif(exam_selected == 'C'):
        e_exam_selected.exam_selected = ExamPaper.SELECTED_C
    else:
        e_exam_selected.exam_selected = ExamPaper.SELECTED_D
        
    e_exam_selected.save()
    
    return  HttpResponse(json.dumps({'response_content':'success'}),mimetype="application/json")
    
    
def exam_grade(paper_id,user):
    user = user
    problem_list = ExamPaper.objects.filter(paper_id=paper_id)
    grade_p = 0
    grade_total=0
    for g in problem_list:
        grade_p=0
        if (g.exam_answer==g.exam_selected):
            grade_p=ExamPaper.objects.get(id=g.id).exam_problem_score
        grade_total=grade_total+grade_p
    problem_count=len(problem_list)
    write_exam_user(paper_id,user,grade_total,problem_count)
    return grade_total
    
def write_exam_user(paper_id,user,grade_total,problem_count):
    paper_id = paper_id
    user = user
    grade_total = grade_total
    problem_count = problem_count
    
    e_exam_user,state = ExamUser.objects.get_or_create(user=user,
                                                       paper_id=paper_id,
                                                       exam_grade=grade_total,
                                                       exam_selected_num=problem_count)
    e_exam_user.save()
    return ''

#@staff_member_required                    
@csrf_exempt      
def exam_end(request):
    a=0
    return render_to_response('examination/exam_end.html',{'a':a,},context_instance=RequestContext(request))

