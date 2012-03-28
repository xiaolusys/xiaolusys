

def access_control_allow_origin(func):
    def _warp(*args,**kwargs):

        response = func(*args,**kwargs)
        response['Access-Control-Allow-Origin'] = '*'

        return response
    return _warp
  