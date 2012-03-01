import json
import datetime
from subway.models import Hotkey, KeyScore

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def hotkeys(request):
    SRH_WRD=1; SRH_PPL=2; SRH_TMS=3; CLK_TMS=4; MAL_CLK=5; CML_CLK=6; NUM_TRD=8; PRICE=10

    datatype = request.POST.get("type")
    keystr = request.POST.get("hotkeys")
    
    if datatype == "search":
        SRH_PPL=7; SRH_TMS=2; PRICE=11;

    keys = json.loads(keystr)

    n = keys[0][-1]
    for i in range(0,n):
        item = keys[0][i]
        try:
            exist_item = Hotkey.objects.get(word=item[SRH_WRD])
            if exist_item.updated + datetime.timedelta(days=1) < datetime.datetime.now():
                exist_item.update(
                    num_people=item[SRH_PPL],
                    num_search=item[SRH_TMS],num_click=item[CLK_TMS],
                    num_tmall_click=item[MAL_CLK],num_cmall_click=item[CML_CLK],
                    num_trade=item[NUM_TRD],ads_price_cent=item[PRICE]*100)
        except Hotkey.DoesNotExist:
            add_item = Hotkey.objects.create(
                word=item[SRH_WRD],num_people=item[SRH_PPL],
                num_search=item[SRH_TMS],num_click=item[CLK_TMS],
                num_tmall_click=item[MAL_CLK],num_cmall_click=item[CML_CLK],
                num_trade=item[NUM_TRD],ads_price_cent=item[PRICE]*100)
            add_item.save()

    return HttpResponse(json.dumps({"code":0}))


def selectkeys(request):
    num_keys = request.GET.get("num", 20)
    excludes = request.GET.get("excludes", None)
    prod_id = request.GET.get("prod_id", None)
    is_tmall = request.GET.get("tmall", False)

    if prod_id is None:
        return HttpResponse(json.dumps({"code": 1, "error": "no product id"}))

    if excludes is not None:
        excludes = excludes.split(',')
        num_keys += len(excludes)

    #if is_tmall:
    #    keys = Hotkey.objects.all().order_by('-num_tmall_click','')
    #
    #ks_items = KeyScore.objects.filter(prod_id=prod_id)[:num_keys]
    return HttpResponse("done")
    
    
