#-*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Sum,Count
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from shopback.base.authentication import login_required_ajax
from shopapp.comments.models import Comment,CommentGrade
from django.template import RequestContext 
import logging
from django.contrib.auth.models import User


logger = logging.getLogger('django.request')


@login_required_ajax
def comment_not_need_explain(request,id):
    
    rows =  Comment.objects.filter(id = id).update(ignored = True)
    
    return  HttpResponse(json.dumps({'code':(1,0)[rows]}),mimetype="application/json")


@csrf_exempt
@login_required_ajax
def explain_for_comment(request):
    
    content = request.REQUEST
    cid     = content.get('cid')
    reply   = content.get('reply')
    
    try:
        comment = Comment.objects.get(id=cid)
    
        comment.reply_order_comment(reply,request.user)
    except Exception,exc:
        logger.error(exc.message or str(exc),exc_info=True)
        return HttpResponse(json.dumps({'code':1,'error_response':exc.message}),mimetype="application/json")
    
    return  HttpResponse(json.dumps({'code':0,'response_content':'success'}),mimetype="application/json")
    
    
def filter_calcCommentCountJson(fdt,tdt):
#这里是构造数据字典格式
    """
        {'vikey':{'20140304':2}}    
    """
    comment_dict = {}
    comments = Comment.objects.filter(
        replay_at__gte=fdt,replay_at__lte=tdt,is_reply=True)
    
    for c in comments:
        try:
            replayer = c.replayer
        except:
            continue
        day_date = c.replay_at.strftime('%Y%m%d')
        if comment_dict.has_key(replayer):
            comment_dict[replayer][day_date] = comment_dict[replayer].get(day_date,0)+1
        else:
            comment_dict[replayer] = {day_date:1}
            
    return comment_dict   

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
    content  =  request.POST
    fromDate = content.get('fromDate')
    toDate   = content.get('toDate')
   
    toDate   = toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or datetime.datetime.now().date()
    oneday = datetime.timedelta(days=1)
#防止每次submint页面日期自动自加,
    toDate_cheak = toDate+oneday
#   搜索日期截至日为方便查询，自动加一天，因为截至是每天零点，
    fromDate = (fromDate and 
                datetime.datetime.strptime(fromDate, '%Y%m%d').date() or
                toDate_cheak - datetime.timedelta(days=1))  
#   input 保留查询日期
    fromDateShow = fromDate.strftime('%Y%m%d')
    toDateShow   = toDate.strftime('%Y%m%d')
#    print 'fromDateShow',fromDateShow
          
    commentDict = filter_calcCommentCountJson(fromDate,toDate_cheak)
    date_array  = []
    
#   时间条
    resultDict  = {}
    for d in range(0,(toDate_cheak-fromDate).days):
        
        day_str = (fromDate+datetime.timedelta(days=d)).strftime('%Y%m%d')
        date_array.append(day_str)
        
        for name,data in commentDict.iteritems():
            
            day_count = data.get(day_str,0)
            if resultDict.has_key(name):
                resultDict[name].append(day_count)
            else:
                resultDict[name] = [day_count]
            
    for name ,vl in resultDict.iteritems():
#        just for append in values at form
        a=[sum(vl),0]
        vl.append(a)
      
#构造‘key，[val+sum]’的字典
    d = None
    c = []

    for user_key,count_list in resultDict.iteritems():
        d = []
        for index,val in enumerate(date_array):
            c=[count_list[index],val]
            d.append(c)
#下面是加上没有参与添加日期的“总和”
#重新构造‘key，[val]，[sum]’的字典
        
        resultDict[user_key] = [d,(count_list[index+1])]
    
    return render_to_response('comments/comment_counts.html', 
                              {'data': resultDict, 'dates':date_array,
                               'toDate':toDate,'fromDate':fromDate,
                               'fromDateShow':fromDateShow,
                               'toDateShow':toDateShow,},  context_instance=RequestContext(request))

def filter_replyer(name,fdt,tdt):
#def filter_replyer(oid):
    try:
        replyer_comment = {}
        replyer = User.objects.get(username = name )
#评论人过滤器        
        comments = Comment.objects.filter(
            replayer=replyer
            ,replay_at__gte=fdt,
            replay_at__lte=tdt,
            is_reply=True
            )
    
        for r in comments:
        
            replyer = r.replayer
            oid     = r.oid
            item_pic_url = r.item_pic_url
            content      = r.content
            detail_url   = r.detail_url
            reply        = r.reply 
            replayer        = r.replayer 
            if replyer_comment.has_key(replyer):
                replyer_comment[replyer].append((item_pic_url,detail_url,content,reply,oid,replayer))
            else:
                replyer_comment[replyer] = [(item_pic_url,detail_url,content,reply,oid,replayer)]  

    except:
        pass
    return replyer_comment
    
@csrf_exempt
def replyer_detail(request):
    content = request.GET
    name = content.get('replyer')
    fromDate  = content.get('fdt').replace('-','')
    oneday = datetime.timedelta(days=1)
    
    toDate  = content.get('tdt')

    if toDate=="":
        toDate=datetime.date.today().strftime('%Y%m%d')
    else:
        toDate  = content.get('tdt')

    toDate   = toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or datetime.datetime.now().date()
    toDate = toDate+oneday
    fromDate = fromDate and datetime.datetime.strptime(fromDate, '%Y%m%d').date() or toDate - datetime.timedelta(days=1)
    
    replyerDetail = filter_replyer(name,fromDate,toDate)

    return render_to_response('comments/comment_replyer_detail.html',{'replyerDetail':replyerDetail,'replyer':name},context_instance=RequestContext(request))

 
@csrf_exempt   
def write_grade(request):
    
    content=request.GET
    oid = content.get('oid')
    grade = content.get('grade')
    
    
    grader = request.user

    comment = Comment.objects.get(oid=oid)
    num_iid = comment.num_iid
    tid     = comment.tid
    oid     = comment.oid
    reply   = comment.reply
    replayer  = comment.replayer
    
    print reply
    print oid, grade, grader
    
    c_grade,state = CommentGrade.objects.get_or_create(num_iid=num_iid,tid=tid,oid=oid)
    c_grade.replayer = replayer
    c_grade.grader   = request.user
    c_grade.reply    = reply
 
    if (grade == 'good'):
        c_grade.grade = CommentGrade.GRADE_GOOD
    
    else:
        c_grade.grade = CommentGrade.GRADE_BAD

    c_grade.save()

    
    return  HttpResponse(json.dumps({'response_content':'success'}),mimetype="application/json")

    
    