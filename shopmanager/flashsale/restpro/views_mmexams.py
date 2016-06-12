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
from flashsale.mmexam.models import Question, Result
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


class MmexamsViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = serializers.QuestionSerialize
    authentication_classes = (authentication.SessionAuthentication, authentication.BasicAuthentication)
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (renderers.JSONRenderer, renderers.BrowsableAPIRenderer,)
    sheaves = 'sheaves_1'  # 初始化选择的考试轮数

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
        info = constants.MM_EXAM_INFO[self.sheaves]
        customer = get_customer(request)
        xlmm = customer.getXiaolumm()
        is_xlmm = 1 if xlmm else 0  # 是否是小鹿妈妈
        fans_num = xlmm_fans_num(xlmm)
        invite_num = xlmm_invite_num(xlmm)
        exam_result = Result.objects.filter(customer_id=customer.id, sheaves=info['sheaves'])  # 获取对应考试轮数的考试结果
        res_info = collections.defaultdict(exam_date='', total_point=0.0, exam_state=0)
        if exam_result:
            res_info.update(model_to_dict(exam_result, exclude=['customer_id', 'xlmm_id', 'daili_user', 'sheaves']))
        info.update(res_info)
        info.update({"fans_num": fans_num, "invite_num": invite_num, "is_xlmm": is_xlmm})
        return Response(info)

    def get_current_exams_questions(self):
        now = datetime.datetime.now()
        info = constants.MM_EXAM_INFO[self.sheaves]
        start_time = datetime.datetime.strptime(info['start_time'], '%Y-%m-%d %H:%M:%S')
        expire_time = datetime.datetime.strptime(info['expire_time'], '%Y-%m-%d %H:%M:%S')
        if not (start_time < now < expire_time):
            return self.queryset.none()
        return self.queryset.filter(sheaves=info['sheaves'])

    @list_route(methods=['get'])
    def get_single_choices(self, request):
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
        queryset = self.get_current_exams_questions().filter(question_types=Question.SINGLE).order_by("id")

        point = constants.MM_EXAM_INFO[self.sheaves]['single_point']  # 单选题分值
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
        customer = get_customer(request)
        if not customer:
            return Response({"code": 1, "info": "请登陆后重试！"})
        default_result = {"result_point": 0, "is_passed": 0}
        content = request.REQUEST
        question_ids = content.keys()
        qus_rs = self.queryset.filter(id__in=question_ids).values("id", "real_answer", 'question_types')  # 题库
        result_point = 0.0
        question_type_map = {
            1: 'single_point',
            2: 'multiple_point',
            3: 'judge_point'
        }
        sheaves_info = constants.MM_EXAM_INFO[self.sheaves]

        for question_id in question_ids:
            target_qr = qus_rs.filter(id=question_id)
            if target_qr.exists():
                if set(content[question_id]) == set(target_qr[0]['real_answer']):  # 与正确答案相等　则加分
                    point = sheaves_info[question_type_map[qus_rs[0]['question_types']]]
                    result_point = result_point + point
        is_passed = 1 if result_point >= sheaves_info['past_point'] else 0  # 如果指定大于指定的分数则通过
        xlmm = customer.getXiaolumm()
        if not xlmm:
            return Response({"code": 2, "info": "请申请成为小鹿妈妈后参加考试！"})

        result = Result.objects.filter(
            customer_id=customer.id,
            sheaves=sheaves_info['sheaves']
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
                sheaves=sheaves_info['sheaves'],
                total_point=result_point
            )
            result.save()
        default_result.update({"result_point": result_point, "is_passed": is_passed})
        return Response(default_result)

    def create(self, request, *args, **kwargs):
        raise APIException('method not allowed')
