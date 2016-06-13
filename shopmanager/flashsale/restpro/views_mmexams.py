# coding=utf-8
import logging
import datetime
import collections
from django.forms import model_to_dict
from rest_framework import viewsets
from flashsale.mmexam import serializers
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.exceptions import APIException
from flashsale.pay.models_user import Customer
from flashsale.mmexam.models import Question, Result, Mamaexam
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
    now = datetime.datetime.now()
    return Mamaexam.objects.filter(valid=True, start_time__lte=now, expire_time__gte=now,
                                   participant=constants.XLMM_EXAM).first()


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
        xlmm = customer.getXiaolumm()
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
        if not question_id:  # 第一题
            question = queryset.first()
            next_question = queryset.filter(id__gt=question.id).first()
            if next_question:
                default_questoion.update({'next_id': next_question.id})
            serializer = self.get_serializer(question)
            question_content = serializer.data
            default_questoion.update({"question_content": question_content})
            return Response(default_questoion)

        question = queryset.filter(id=question_id).first()
        if not question:
            return Response({})
        next_question = queryset.filter(id__gt=question.id).first()
        previous_question = queryset.filter(id__lt=question.id).first()

        if previous_question:
            default_questoion.update({'previous_id': previous_question.id})
        if next_question:
            default_questoion.update({'next_id': next_question.id})
        serializer = self.get_serializer(question)
        question_content = serializer.data
        default_questoion.update({"question_content": question_content})
        return Response(default_questoion)

    @list_route(methods=['get', 'post'])
    def computation_result(self, request):
        """
        计算：　题号--> 答案 ＝　分值
        返回: 总分　是否通过
        """
        default_result = {"result_point": 0, "is_passed": 0}
        customer = get_customer(request)
        if not customer:
            return Response({"code": 1, "info": "请登陆后重试！", "exam_result": default_result})
        mmexam = get_xlmm_exam()
        if not mmexam:
            return Response({"code": 3, "info": "没有开放的考试！", "exam_result": default_result})
        xlmm = customer.getXiaolumm()
        if not xlmm:
            return Response({"code": 2, "info": "请申请成为小鹿妈妈后参加考试！", "exam_result": default_result})
        content = request.REQUEST
        question_ids = content.keys()
        qus_rs = self.queryset.filter(id__in=question_ids,
                                      sheaves=mmexam.sheaves).values("id",
                                                                     "real_answer",
                                                                     'question_types')  # 题库
        result_point = 0.0
        for question_id in question_ids:
            target_qr = qus_rs.filter(id=question_id)
            if target_qr.exists():
                if set(content[question_id]) == set(target_qr[0]['real_answer']):  # 与正确答案相等　则加分
                    question_types = qus_rs[0]['question_types']
                    point = mmexam.get_question_type_point(question_types)
                    result_point = result_point + point
        is_passed = 1 if result_point >= mmexam.past_point else 0  # 如果指定大于指定的分数则通过

        result = Result.objects.filter(
            customer_id=customer.id,
            sheaves=mmexam.sheaves
        ).first()
        update_fields = []
        if result:
            if is_passed == 1 and result.exam_state != Result.FINISHED:  # 考试通过
                result.exam_state = Result.FINISHED
                update_fields.append("exam_state")
            if result.total_point != result_point:
                result.total_point = result_point
                update_fields.append("total_point")
            if update_fields:
                result.save(update_fields=update_fields)
        else:
            result = Result(
                customer_id=customer.id,
                xlmm_id=xlmm.id,
                daili_user=xlmm.openid,
                sheaves=mmexam.sheaves,
                total_point=result_point
            )
            if is_passed == 1:
                result.exam_state == Result.FINISHED
            result.save()
        if result.exam_state == Result.FINISHED:  # 考试通过　修改代理等级
            if xlmm.agencylevel < mmexam.upper_agencylevel:  # 当前等级小于考试通过指定的等级则升级
                xlmm.agencylevel = mmexam.upper_agencylevel
                xlmm.save(update_fields=['agencylevel'])
        return Response({"code": 0, "info": "考试完成！",
                         "exam_result": {"result_point": result_point,
                                         "is_passed": is_passed}})

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed')
