from rest_framework import exceptions
import logging
logger = logging.getLogger('restapi.errors')

def rest_exception(errmsg=''):
    def _func_wrapper(func):
        def _wrapper(*args,**kwargs):
            
            try:
                return func(*args,**kwargs)
            except Exception,exc:
                logger.error(exc.message ,exc_info=True)
                err_msg = errmsg or exc.message or ''
                raise exceptions.APIException(err_msg)
            
        return _wrapper
    return _func_wrapper