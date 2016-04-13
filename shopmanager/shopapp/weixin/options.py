from .models import WeixinUnionID


def get_unionid_by_openid(openid, appkey):
    wxunoinids = WeixinUnionID.objects.filter(openid=openid, app_key=appkey)
    if wxunoinids.exists():
        return wxunoinids[0].unionid
    return ''


def get_openid_by_unionid(unionid, appkey):
    wxunoinids = WeixinUnionID.objects.filter(unionid=unionid, app_key=appkey)
    if wxunoinids.exists():
        return wxunoinids[0].openid
    return ''
