import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from auth import apis
from shopback.items.models import Item
from shopback.users.models import User
from shopback.items.tasks import updateItemsInfoTask
import logging

logger = logging.getLogger('outeridmultiple')

def updateItems(request):

    visitor_id = request.session['top_parameters']['visitor_id']
    top_session = request.session['top_session']

    onsaleItems = apis.taobao_items_onsale_get(session=top_session,page_no=1,page_size=200)

    items = []

    if onsaleItems.has_key('items_onsale_get_response'):
        if onsaleItems['items_onsale_get_response'].get('total_results',0)>0:
            items.extend(onsaleItems['items_onsale_get_response']['items']['item'])

    user = User.objects.get(visitor_id=visitor_id)
    user.update_items_datetime = datetime.datetime.now()
    user.save()

    for item in items:
        try:
            itemobj = Item.objects.get(outer_iid=item['outer_id'],user_id=visitor_id)

            if itemobj.num_iid  != str(item['num_iid']):
                logger.error('Outer_iid multiple to items(outer_iid:%s,num_iid:%s)' %(item['outer_id'],item['num_iid']))
                continue
        except Item.DoesNotExist:

            itemobj = Item()
            itemobj.outer_iid = item['outer_id']
            itemobj.user_id = visitor_id

        for k,v in item.iteritems():
            hasattr(itemobj,k) and setattr(itemobj,k,v)

        itemobj.save()

    updateItemsInfoTask.delay(visitor_id)

    response = {'pulled':len(items)}

    return HttpResponse(json.dumps(response),mimetype='application/json')

  