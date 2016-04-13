# -*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Sum, Count
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from shopback.base.authentication import login_required_ajax
from shopapp.comments.models import Comment, CommentGrade
from django.template import RequestContext
import logging
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required

logger = logging.getLogger('django.request')


@login_required_ajax
def comment_not_need_explain(request, id):
    rows = Comment.objects.filter(id=id).update(ignored=True)

    return HttpResponse(json.dumps({'code': (1, 0)[rows]}), content_type="application/json")


@csrf_exempt
@login_required_ajax
def explain_for_comment(request):
    content = request.REQUEST
    cid = content.get('cid')
    reply = content.get('reply')

    try:
        comment = Comment.objects.get(id=cid)

        comment.reply_order_comment(reply, request.user)
    except Exception, exc:
        logger.debug(u'评价异常:%s' % exc.message)
        return HttpResponse(json.dumps({'code': 1,
                                        'error_response': exc.message}),
                            content_type="application/json")

    return HttpResponse(json.dumps({'code': 0,
                                    'response_content': 'success'}),
                        content_type="application/json")


def filter_calcCommentCountJson(fdt, tdt):
    # 这里是构造数据字典格式
    """
        {'vikey':{'20140304':2}}   
    """

    array_comment_and_grade = []
    comment_dict = {}
    good_show = ''
    bad_show = ''
    normal_show = ''

    comments = Comment.objects.filter(
        replay_at__gte=fdt, replay_at__lte=tdt, is_reply=True)

    for c in comments:
        try:
            replayer = c.replayer
        except:
            continue
        day_date = c.replay_at.strftime('%Y%m%d')
        if comment_dict.has_key(replayer):
            comment_dict[replayer][day_date] = comment_dict[replayer].get(day_date, 0) + 1
        else:
            comment_dict[replayer] = {day_date: 1}
            # 为了把 字典 和 好坏案例 一起提交
    array_comment_and_grade.append(comment_dict)
    #
    good_show = len(CommentGrade.objects.filter(
        grade=1, replay_at__gte=fdt, replay_at__lte=tdt
    ))
    bad_show = len(CommentGrade.objects.filter(
        grade=0, replay_at__gte=fdt, replay_at__lte=tdt
    ))
    normal_show = len(CommentGrade.objects.filter(
        grade=2, replay_at__gte=fdt, replay_at__lte=tdt
    ))

    array_comment_and_grade.append(good_show)
    array_comment_and_grade.append(bad_show)
    array_comment_and_grade.append(normal_show)

    return array_comment_and_grade


""" 
   if 'fromDate' in request.POST:
        
        gg = [10,20,30,40,50,60,70, 280]
        dd = [11,21,31,41,51,61,71, 287]
    
        data = {'gg':gg,'dd':dd}
        dates = [20140403,20140404,20140405,20140406,20140407,20140408,20140409]
    else:
        vicky = [10,20,30,40,50,60,70, 280]
        spring = [11,21,31,41,51,61,71, 287]
    
        data = {'vicky':vicky,'spring':spring}
        dates = [20140403,20140404,20140405,20140406,20140407,20140408,20140409]
"""


#   统计展示每个人的日输出数字        
@csrf_exempt
def count(request):
    #   得到页面信息
    content = request.POST
    fromDate = content.get('fromDate')
    toDate = content.get('toDate')

    toDate = toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or datetime.datetime.now().date()
    oneday = datetime.timedelta(days=1)
    # 防止每次submint页面日期自动自加,toDate_cheak和toDate差一天,
    toDate_cheak = toDate + oneday
    #   搜索日期截至日为方便查询，自动加一天，因为截至是每天零点，
    fromDate = (fromDate and
                datetime.datetime.strptime(fromDate, '%Y%m%d').date() or
                toDate_cheak - datetime.timedelta(days=1))
    #   input 保留查询日期
    fromDateShow = fromDate.strftime('%Y%m%d')
    toDateShow = toDate.strftime('%Y%m%d')
    commentDict = filter_calcCommentCountJson(fromDate, toDate_cheak)

    resultDict = {}
    #   时间条
    date_array = []
    for d in range(0, (toDate_cheak - fromDate).days):
        day_str = (fromDate + datetime.timedelta(days=d)).strftime('%Y%m%d')
        date_array.append(day_str)

        for name, data in commentDict[0].iteritems():
            day_count = data.get(day_str, 0)
            if resultDict.has_key(name):
                resultDict[name].append(day_count)
            else:
                resultDict[name] = [day_count]

    for name, vl in resultDict.iteritems():
        #        just for append in values at form
        a = [sum(vl), 0]
        vl.append(a)
    # 构造‘key，[val+sum]’的字典
    d = None
    c = []

    for user_key, count_list in resultDict.iteritems():
        d = []
        for index, val in enumerate(date_array):
            c = [count_list[index], val]
            d.append(c)
        # 下面是加上没有参与添加日期的“总和”
        # 重新构造‘key，[val]，[sum]’的字典
        resultDict[user_key] = [d, (count_list[index + 1])]

    return render_to_response('comments/comment_counts.html',
                              {'data': resultDict, 'dates': date_array,
                               'toDate': toDate, 'fromDate': fromDate,
                               'fromDateShow': fromDateShow,
                               'toDateShow': toDateShow, 'good_num': commentDict[1],
                               'bad_num': commentDict[2], 'normal_num': commentDict[3], 'toDate_cheak': toDate_cheak,},
                              context_instance=RequestContext(request))


def filter_replyer(name, fdt, tdt):
    # def filter_replyer(oid):
    try:
        replyer_comment = {}
        replyer = User.objects.get(username=name)
        # 评论人过滤器
        comments = Comment.objects.filter(
            replayer=replyer,
            replay_at__gte=fdt,
            replay_at__lte=tdt,
            is_reply=True
        )

        for r in comments:
            # 1:good,0:bad,2:null
            grade = ''
            color = ''
            replyer = r.replayer
            oid = r.oid
            item_pic_url = r.item_pic_url
            content = r.content
            detail_url = r.detail_url
            reply = r.reply
            replayer = r.replayer
            try:
                # if 做try注销后的测试，if (comment_grade==[]):
                #            if (1==1):
                #                这里可能有错,2?
                comment_grade = CommentGrade.objects.filter(
                    oid=oid
                )
                # if (comment_grade==[]): 是错的，但是可以通过try 语句正常 走完
                if (comment_grade == []):
                    grade = 3
                else:
                    grade = comment_grade[0].grade
                    # 查询结果 直接可以改变背景颜色
                    if (grade == 1):
                        color = '#F08080'
                    elif (grade == 0):
                        color = '#E0FFFF'
                    else:
                        color = '#FFE4B5'
            except:
                pass
            if replyer_comment.has_key(replyer):
                replyer_comment[replyer].append((item_pic_url, detail_url, content, reply, oid, replayer, grade, color))
            else:
                replyer_comment[replyer] = [(item_pic_url, detail_url, content, reply, oid, replayer, grade, color)]
    except:
        pass
    return replyer_comment


@csrf_exempt
def replyer_detail(request):
    content = request.GET
    name = content.get('replyer')
    fromDate = content.get('fdt').replace('-', '')
    oneday = datetime.timedelta(days=1)
    toDate = content.get('tdt')

    if toDate == "":
        toDate = datetime.date.today().strftime('%Y%m%d')
    else:
        toDate = content.get('tdt')

    toDate = toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or datetime.datetime.now().date()
    toDate = toDate + oneday
    fromDate = fromDate and datetime.datetime.strptime(fromDate, '%Y%m%d').date() or toDate - datetime.timedelta(days=1)
    #    详情过滤
    replyerDetail = filter_replyer(name, fromDate, toDate)

    return render_to_response('comments/comment_replyer_detail.html', {'replyerDetail': replyerDetail, 'replyer': name},
                              context_instance=RequestContext(request))


@csrf_exempt
def write_grade(request):
    content = request.GET
    oid = content.get('oid')
    grade = content.get('grade')
    comment = Comment.objects.get(oid=oid)
    num_iid = comment.num_iid
    tid = comment.tid
    oid = comment.oid
    reply = comment.reply
    replayer = comment.replayer
    replay_at = comment.replay_at
    content = comment.content

    c_grade, state = CommentGrade.objects.get_or_create(num_iid=num_iid, tid=tid, oid=oid)
    c_grade.replayer = replayer

    c_grade.grader = request.user
    c_grade.reply = reply
    c_grade.replay_at = replay_at

    if (grade == 'good'):
        c_grade.grade = CommentGrade.GRADE_GOOD
    elif (grade == 'normal'):
        c_grade.grade = CommentGrade.GRADE_NORMAL
    else:
        c_grade.grade = CommentGrade.GRADE_BAD

    c_grade.save()

    return HttpResponse(json.dumps({'response_content': 'success'}), content_type="application/json")


def grade_show_filter(grade, replay_at__gte, toDate_cheak):
    #    如要返回：图片  item_pic_url，图片链接地址    detail_url，客人评价    content，客服评价    reply，打分    grade
    #   通过 CommentGrade.objects.filter 过滤 grade=1 的oid，得到集合oid_arrays
    #   通过 Comment。objectd.filter 过滤 oid——arrays里面的 oid，得到字典

    dic_grade_show = {}

    grade_filter = CommentGrade.objects.filter(grade=grade, replay_at__gte=replay_at__gte, replay_at__lte=toDate_cheak)

    for o in grade_filter:
        comment_filter_grade_show = Comment.objects.filter(oid=o.oid)
        dic_grade_show[o.oid] = [comment_filter_grade_show[0].item_pic_url,
                                 comment_filter_grade_show[0].detail_url,
                                 comment_filter_grade_show[0].content,
                                 comment_filter_grade_show[0].reply,
                                 comment_filter_grade_show[0].replayer,
                                 o.grader,
                                 comment_filter_grade_show[0].oid]
    return dic_grade_show


@csrf_exempt
@staff_member_required
def replyer_grade(request):
    #    如要返回：图片  item_pic_url，图片链接地址    detail_url，客人评价    content，客服评价    reply，打分    grade
    #   得到页面信息
    #   调用grade_show_filter()方法，
    content = request.GET
    replay_at__gte = content.get('from').replace('-', '')
    replay_at__lte = content.get('to').replace('-', '')
    grade = content.get('grade')
    grade_show = ''
    color = ''

    replay_at__lte = replay_at__lte and datetime.datetime.strptime(replay_at__lte,
                                                                   '%Y%m%d').date() or datetime.datetime.now().date()
    oneday = datetime.timedelta(days=1)
    # 防止每次submint页面日期自动自加,toDate_cheak和toDate差一天,
    toDate_cheak = replay_at__lte + oneday
    #   搜索日期截至日为方便查询，自动加一天，因为截至是每天零点，
    replay_at__gte = (replay_at__gte and
                      datetime.datetime.strptime(replay_at__gte, '%Y%m%d').date() or
                      toDate_cheak - datetime.timedelta(days=1))
    #   input 保留查询日期
    reply_grade_arrays = grade_show_filter(grade, replay_at__gte, toDate_cheak)

    if grade == '1':
        grade_show = '优秀'
        color = '#A52A2A'
    elif grade == '0':
        grade_show = '不合格'
        color = '#87CEFA'
    else:
        grade_show = '合格'
        color = '#B8860B'

    return render_to_response('comments/comment_replyer_grade.html',
                              {'reply_grade_arrays': reply_grade_arrays, 'grade_show': grade_show, 'color': color,},
                              context_instance=RequestContext(request))
