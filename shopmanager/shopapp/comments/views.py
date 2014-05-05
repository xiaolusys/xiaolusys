#-*- encoding:utf8 -*-
import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Sum,Count
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from shopback.base.authentication import login_required_ajax
from shopapp.comments.models import Comment
from django.template import RequestContext 
import logging
from django.contrib.auth.models import User,Group


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
    
    
def calcCommentCountJson(fdt,tdt):
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
        
@csrf_exempt
def count(request):
   
    
    content  =  request.POST
    fromDate = content.get('fromDate')
    toDate   = content.get('endDate')
    
    toDate   = toDate and datetime.datetime.strptime(toDate, '%Y%m%d').date() or datetime.datetime.now().date()
        
    fromDate = fromDate and datetime.datetime.strptime(fromDate, '%Y%m%d').date() or toDate - datetime.timedelta(days=1)  
          
    
    commentDict = calcCommentCountJson(fromDate,toDate)
    #print 'commentDict',commentDict
    date_array  = []
    resultDict  = {}
    for d in range(0,(toDate-fromDate).days):
        
        day_str = (fromDate+datetime.timedelta(days=d)).strftime('%Y%m%d')
        date_array.append(day_str)
        
        for name,data in commentDict.iteritems():
            
            day_count = data.get(day_str,0)
            if resultDict.has_key(name):
                resultDict[name].append(day_count)
            else:
                resultDict[name] = [day_count]
            
    for name ,vl in resultDict.iteritems():
        vl.append(sum(vl))
    
    return render_to_response('comments/comment_counts.html', {'data': resultDict, 'dates':date_array},  context_instance=RequestContext(request))



def filter_replyer(name):
    try:

        replyer_comment = {}
        replyer = User.objects.get(username = name )        
        comments = Comment.objects.filter(
        replayer=replyer)        
    
        for r in comments:
        
            replyer = r.replayer
            if replyer_comment.has_key(replyer):
                replyer_comment[replyer].append(r.reply)
            else:
                    replyer_comment[replyer] = [r.reply]        
    except:
        pass
    return replyer_comment
    
@csrf_exempt
def replyer_detail(request):
    content = request.GET
    name = content.get('replyer')
    replyerDetail = filter_replyer(name)
    
    #oo = show_replyer(request)
    #print oo
    #print 'ooooooooooooooooooooo'
    return render_to_response('comments/comment_detail.html',{'replyerDetail':replyerDetail,'replyer':name},context_instance=RequestContext(request))
    
def show_replyer(request):
    comment_array = []
    comments = User.objects.filter(groups=u'kefu')
    #comments = User.objects.all()
    
    print 'ooccccccccccccc'
    #print 
    print comments
    
    print 'ccccccccccccccccccccc'
    for c in comments:
        try:
            replyer = c.username
            comment_array.append(replyer)
        except:
            continue
    
    return comment_array   