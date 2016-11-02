# coding=utf-8
import logging
import datetime
import collections
from django.forms import model_to_dict
from django.db.models import Sum
from rest_framework import viewsets
from flashsale.mmexam import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.exceptions import APIException
from flashsale.pay.models import Customer
from flashsale.mmexam.models import Question, Result, Mamaexam, ExamResultDetail
from flashsale.mmexam import constants

logger = logging.getLogger(__name__)


def get_customer(request):
    customer = Customer.objects.filter(user=request.user, status=Customer.NORMAL).first()
    return customer


def xlmm_fans_num(xlmm):
    if xlmm and xlmm.mama_fortune:
        return xlmm.mama_fortune.fans_num
    return 0


def xlmm_invite_num(xlmm):
    if xlmm and xlmm.mama_fortune:
        return xlmm.mama_fortune.invite_num
    return 0


def get_xlmm_exam():
    #now = datetime.datetime.now()
    # return Mamaexam.objects.filter(valid=True, start_time__lte=now, expire_time__gte=now,
    #                                participant=constants.XLMM_EXAM).first()
    return Mamaexam.objects.filter(valid=True, participant=constants.XLMM_EXAM).order_by('-start_time').first()


def computation_practice_point(xlmm):
    """ 计算实践部分的分数 """
    fans_num = xlmm_fans_num(xlmm)
    invite_num = xlmm_invite_num(xlmm)
    invite_point = 31 if invite_num >= 8 else 0  # 邀请：31分（只有达到成功邀请8人才得到这部分的31分）
    fans_point = min(14.0, fans_num * 0.7)  # 分享：14分 # 每题　0.7 分最高14分　按分享人数比例计算
    return invite_point + fans_point  # 实践分数


def get_user_answer(customer_id, question_id):
    """ 获取用户的回答 """
    cus_answer = ExamResultDetail.customer_answer(customer_id, question_id)  # 用户回答
    user_answer_serializer = serializers.ExamResultDetailSerialize(cus_answer)
    return user_answer_serializer.data


class MmexamsViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = serializers.QuestionSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    # renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)

    @list_route(methods=['get'])
    def get_start_page_info(self, request):
        """
        考试轮数
        开始时间
        结束时间
        粉丝数量
        邀请数量
        考试结果
        """
        exam = get_xlmm_exam()
        if not exam:
            return Response({"code": 1, "info": "暂时没有开放的考试", "exam_info": ''})
        mm_exam = model_to_dict(exam)
        customer = get_customer(request)
        if not customer:
            return Response({"code": 2, "info": "请登陆后重试!", "exam_info": ''})
        xlmm = customer.get_charged_mama()
        is_xlmm = 1 if xlmm else 0  # 是否是小鹿妈妈
        fans_num = xlmm_fans_num(xlmm)
        invite_num = xlmm_invite_num(xlmm)

        exam_result = Result.objects.filter(customer_id=customer.id, sheaves=exam.sheaves).first()  # 获取对应考试轮数的考试结果
        res_info = collections.defaultdict(exam_date='', total_point=0.0, exam_state=0)
        if exam_result:
            res_info.update(model_to_dict(exam_result, exclude=['customer_id', 'xlmm_id', 'daili_user', 'sheaves']))
        mm_exam.update(res_info)
        mm_exam.update({"fans_num": fans_num, "invite_num": invite_num, "is_xlmm": is_xlmm})
        return Response({"code": 0, "info": "获取用户考试信息成功", "exam_info": mm_exam})

    def get_current_exams_questions(self, exam):

        if exam:
            return self.queryset.filter(sheaves=exam.sheaves)
        return self.queryset.none()

    @list_route(methods=['get'])
    def get_mmexam_question(self, request):
        """
        总题目数量
        分值
        总分
        当前第几题
        当前题目
        当前选项
        上一题号
        下一题号
        """
        content = request.REQUEST
        question_id = content.get('question_id') or None
        question_types = content.get('question_type') or None
        question_types_map = {
            1: Question.SINGLE,
            2: Question.MANY,
            3: Question.TUFA
        }
        if not question_types:
            return Response({})
        if int(question_types) not in question_types_map.keys():
            return Response({})
        mmexam = get_xlmm_exam()
        queryset = self.get_current_exams_questions(exam=mmexam).filter(
            question_types=question_types_map[int(question_types)]).order_by("id")

        point = mmexam.single_point  # 单选题分值
        question_count = queryset.count()  # 总题目数量
        total_point = point * question_count  # 总分
        default_questoion = collections.defaultdict(
            point=point,
            question_count=question_count,
            total_point=total_point,
            current_no=1,
            previous_id=None,
            next_id=None,
            question_content={}
        )
        if not queryset.exists():
            return Response(default_questoion)
        customer = get_customer(request)
        if not question_id:  # 第一题
            question = queryset.first()
            if not question:
                return Response({})
            next_question = queryset.filter(id__gt=question.id).first()
            if next_question:
                default_questoion.update({'next_id': next_question.id})
            serializer = self.get_serializer(question)
            question_content = serializer.data
            user_answer = get_user_answer(customer.id, question.id)
            default_questoion.update({"question_content": question_content, "user_answer": user_answer})
            return Response(default_questoion)

        question = queryset.filter(id=question_id).first()
        if not question:
            return Response({})
        ids = map(lambda x: x['id'], queryset.values('id'))  # 取出来id
        default_questoion.update({'current_no': ids.index(question.id) + 1})  # 更新当前的题号
        next_question = queryset.filter(id__gt=question.id).first()
        previous_question = queryset.filter(id__lt=question.id).first()

        if previous_question:
            default_questoion.update({'previous_id': previous_question.id})
        if next_question:
            default_questoion.update({'next_id': next_question.id})
        serializer = self.get_serializer(question)
        question_content = serializer.data

        user_answer = get_user_answer(customer.id, question.id)
        default_questoion.update({"question_content": question_content, "user_answer": user_answer})
        return Response(default_questoion)

    @list_route(methods=['get', 'post'])
    def create_answer_detail(self, request):
        """
        添加答题明细
        """
        customer = get_customer(request)
        if not customer:
            return Response({"code": 1, "info": "请登陆后重试！"})
        mmexam = get_xlmm_exam()
        if not mmexam:
            return Response({"code": 2, "info": "没有开放的考试！"})
        xlmm = customer.get_charged_mama()
        if not xlmm:
            return Response({"code": 3, "info": "请申请成为小鹿妈妈后参加考试！"})
        content = request.REQUEST
        question_id = content.get("question_id") or None
        answer = content.get("answer") or None
        if not (question_id and answer):
            return Response({"code": 4, "info": "回答不能为空！"})
        question = self.queryset.filter(id=question_id, sheaves=mmexam.sheaves).first()  # 试题
        if not question:
            return Response({"code": 5, "info": "题目不存在！"})
        res_detail = ExamResultDetail.objects.filter(customer_id=customer.id, question_id=question_id).first()
        is_right = True if set(question.real_answer) == set(answer) else False  # 答案和回答集合相等认为正确
        point = mmexam.get_question_type_point(question.question_types)
        if res_detail:
            detail_update_fields = []
            if res_detail.answer != answer:
                res_detail.answer = answer
                detail_update_fields.append('answer')
            if res_detail.is_right != is_right:
                res_detail.is_right = is_right
                detail_update_fields.append('is_right')
            if detail_update_fields:
                res_detail.save(update_fields=detail_update_fields)
        else:
            res_detail = ExamResultDetail(customer_id=customer.id,
                                          sheaves=mmexam.sheaves,
                                          question_id=question_id,
                                          answer=answer,
                                          is_right=is_right,
                                          point=point,
                                          uni_key=str(customer.id) + '/' + str(question_id))
            res_detail.save()
        return Response({"code": 0, "info": "答题成功！"})

    @list_route(methods=['get', 'post'])
    def computation_result(self, request):
        """
        计算结果：考试结果　最后一题　计算总分 考核是否升级
        """
        default_result = {"total_point": 0, "is_passed": 0}
        customer = get_customer(request)
        xlmm = customer.get_charged_mama()
        if not customer:
            return Response({"code": 1, "info": "请登陆后重试！",
                             "exam_result": default_result})
        if not xlmm:
            return Response({"code": 2, "info": "请申请成为小鹿妈妈后参加考试！",
                             "exam_result": default_result})
        content = request.REQUEST
        sheaves = content.get("sheaves") or None
        now = datetime.datetime.now()
        exam = Mamaexam.objects.filter(sheaves=sheaves, valid=True, start_time__lte=now, expire_time__gte=now).first()
        if not exam:
            return Response({"code": 2, "info": "考试已经结束！",
                             "exam_result": default_result})
        exam_details = ExamResultDetail.objects.filter(customer_id=customer.id, sheaves=sheaves, is_right=True)  # 正确的答题
        result_point = exam_details.aggregate(s_point=Sum('point')).get('s_point') or 0  # 答题分数
        practive_point = computation_practice_point(xlmm)  # 实践部分得分
        total_point = result_point + practive_point

        is_passed = 1 if total_point >= exam.past_point else 0  # 如果 总分数 大于指定的通过的分数则通过
        result = Result.objects.filter(customer_id=customer.id,
                                       sheaves=exam.sheaves).first()
        update_fields = []
        if result:
            if is_passed == 1 and result.exam_state != Result.FINISHED:  # 考试通过
                result.exam_state = Result.FINISHED
                update_fields.append("exam_state")
            if result.total_point != total_point:
                result.total_point = total_point
                update_fields.append("total_point")
            if update_fields:
                result.modified = datetime.datetime.now()
                update_fields.append('modified')
                result.save(update_fields=update_fields)
        else:
            result = Result(
                customer_id=customer.id,
                xlmm_id=xlmm.id,
                daili_user=xlmm.openid,
                sheaves=exam.sheaves,
                total_point=total_point
            )
            if is_passed == 1:
                result.exam_state = Result.FINISHED
            result.save()
        if result.exam_state == Result.FINISHED:  # 考试通过　修改代理等级
            xlmm.upgrade_agencylevel_by_exam(level=exam.upper_agencylevel)  # 考试通过　调用升级
        return Response({"code": 0, "info": "考试完成！",
                         "exam_result": {"total_point": total_point,
                                         "is_passed": is_passed}})

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed')
