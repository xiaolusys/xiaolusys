import json
import decimal

def access_control_allow_origin(func):
    def _warp(*args,**kwargs):

        response = func(*args,**kwargs)
        response['Access-Control-Allow-Origin'] = '*'

        return response
    return _warp


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,decimal.Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)