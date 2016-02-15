from .models import WeixinUnionID

def get_unoinid_by_openid(openid, appkey):
    wxunoinids = WeixinUnionID.objects.filter(openid=openid,app_key=appkey)
    if wxunoinids.exists():
        return wxunoinids[0].unionid
    return ''