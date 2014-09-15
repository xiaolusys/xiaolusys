#-*- coding:utf-8 -*-
import time
import json
import random
from django.http import HttpResponse
from django.template import RequestContext 
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.db import models
#from django.contrib.admin.views.decorators import staff_member_required

from .models import ExamProblem,ExamPaper,ExamUserPaper,ExamUserProblem
from shopapp.weixin.views import get_user_openid
import logging

logger = logging.getLogger('django.request')

class WeixinExamView(View):
    
    def getRandomProblemByUserPaper(self,exam_user_paper):
        
        answer_problems = ExamUserProblem.objects.filter(user_openid=exam_user_paper.user_openid,
                                                            paper_id=exam_user_paper.paper_id)
        answer_problem_ids = [p.problem_id for p in answer_problems]
        
        unanswer_problems = ExamProblem.objects.filter(status=ExamProblem.ACTIVE).exclude(id__in=answer_problem_ids)
        rand_index = random.randint(0,max(len(unanswer_problems)-1,0))
        
        return unanswer_problems[rand_index]
        
        
    def get(self, request, userpk):
        
        content = request.REQUEST
        code = content.get('code')
        
        user_openid = get_user_openid(request, code)
        #user_openid = 'oMt59uJJBoNRC7Fdv1b5XiOAngdU'
        if not user_openid  or user_openid.upper() == 'NONE':
            return HttpResponse(u'只有微信用户才有答题权限哦')
        
        exam_papers = ExamPaper.objects.filter(status=ExamPaper.ACTIVE)
        if exam_papers.count() <= 0:
            return HttpResponse(u'答题活动还没开始哦')
        
        exam_paper = exam_papers[0]
        exam_user_paper,state = ExamUserPaper.objects.get_or_create(user_openid=user_openid,
                                                              paper_id=exam_paper.id)
        if (exam_user_paper.status == ExamPaper.FINISHED or 
            exam_user_paper.answer_num >= exam_paper.problem_num):
            return render_to_response('weixin/examination/weixin_exam_final.html', 
                                      {"exam_user_paper":exam_user_paper, "userpk":userpk},
                                      context_instance=RequestContext(request))
        
        new_problem = self.getRandomProblemByUserPaper(exam_user_paper)
        
        response = render_to_response('weixin/examination/weixin_exam.html', 
                                      {"problem":new_problem, "exam_user_paper": exam_user_paper,
                                       "userpk":userpk},
                                      context_instance=RequestContext(request))
        return response

    def post(self, request, userpk):
        content = request.REQUEST

        code = content.get('code')
        user_openid = get_user_openid(request, code)
        #user_openid = 'oMt59uJJBoNRC7Fdv1b5XiOAngdU'
        if not user_openid or user_openid.upper() == 'NONE':
            return HttpResponse(u'只有微信用户才有答题权限哦')
        
        paper_id   = content.get('paper_id')
        problem_id = content.get('problem_id')
        selected   = content.get('selected')
        if not selected:
            return HttpResponse(u'请选择答案')
        
        problem = ExamProblem.objects.get(id=problem_id)
        exam_paper = ExamPaper.objects.get(id=paper_id)
        exam_user_paper = ExamUserPaper.objects.get(user_openid=user_openid,paper_id=paper_id)
        
        if exam_user_paper.status == ExamUserPaper.UNFINISHED:
            
            answer_right = problem.problem_answer == selected
            answer_score = answer_right and problem.problem_score or 0
            ExamUserProblem.objects.create(user_openid=user_openid,
                                          paper_id=paper_id,
                                          problem_id=problem_id,
                                          selected=selected,
                                          status=answer_right,
                                          problem_score=answer_score)
            
            ExamUserPaper.objects.filter(user_openid=user_openid,
                        paper_id=paper_id).update(answer_num = models.F('answer_num') + 1,
                                                  grade = models.F('grade') + answer_score)
        
            exam_user_paper = ExamUserPaper.objects.get(user_openid=user_openid,paper_id=paper_id)
            
        if exam_user_paper.answer_num >= exam_paper.problem_num:
            exam_user_paper.status = ExamUserPaper.FINISHED
            exam_user_paper.save()
            return render_to_response('weixin/examination/weixin_exam_final.html', 
                                      {"exam_user_paper":exam_user_paper, "userpk":userpk},
                                      context_instance=RequestContext(request))
        
        new_problem = self.getRandomProblemByUserPaper(exam_user_paper)

        html_block_content = render_to_response('weixin/examination/weixin_exam_block.html', 
                                                {"problem":new_problem, 
                                                 "exam_user_paper": exam_user_paper,
                                                 "userpk":userpk},
                                                context_instance=RequestContext(request))

        if content.get("block") == "yes":
            return html_block_content
        
        response = render_to_response('weixin/examination/weixin_exam.html', 
                                      {"problem":new_problem, 
                                       "exam_user_paper": exam_user_paper},
                                      context_instance=RequestContext(request))
        return response


class WeixinExamShareView(View):
    def get(self, request, userpk):
        content = request.REQUEST
        response = render_to_response('weixin/examination/weixin_exam_share.html', 
                                      {"userpk":userpk},
                                      context_instance=RequestContext(request))
        return response
    
