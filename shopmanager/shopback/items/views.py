import json
import datetime
from django.http import HttpResponse
from django.conf import settings
from auth import apis
from shopback.items.models import Item

def updateItems(request):

    session = request.session

    onsaleItems = apis.taobao_items_onsale_get(session=session['top_session'],page_no=1,page_size=200)

    items = onsaleItems.get('items_onsale_get_response',[]) and onsaleItems['items_onsale_get_response']['items'].get('item',[])

    session['update_items_datetime'] = datetime.datetime.now()

    for item in items:
        try:
            itemobj = Item.objects.get(outer_iid=item['outer_id'])
            itemobj.num = item['num']

            session_keys = json.loads(itemobj.numiid_session)
            session_set = set(session_keys)

            numiid_session = str(item['num_iid'])+':'+session.session_key

            session_set.add(numiid_session)
            itemobj.numiid_session = json.dumps(list(session_set))

            itemobj.save()
        except Item.DoesNotExist:

            itemobj = Item()
            itemobj.outer_iid = item['outer_id']
            itemobj.num = item['num']

            numiid_session = str(item['num_iid'])+':'+session.session_key

            itemobj.numiid_session = json.dumps([numiid_session])
            itemobj.save()

    response = {'updateitemnum':len(items)}

    return HttpResponse(json.dumps(response),mimetype='application/json')

  