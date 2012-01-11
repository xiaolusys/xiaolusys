import json
from django.http import HttpResponse
import logging
logger = logging.getLogger('exception.middleware')

class RecordExceptionMiddleware(object):

    def process_exception(self,request, e):
        """ docstring for process_exception """

        logger.error(logger.error('Error excution handler method(user:%s) details: %s'
                                  % (request.user, e), exc_info=True))
        response = {'error':'Sorry,internal server error!Please contact with the admin.'}
        return HttpResponse(json.dumps(response),mimetype='application/json')
  