import logging
logger = logging.getLogger('exception.middleware')

class RecordExceptionMiddleware(object):

    def process_exception(self,request, e):
        """ docstring for process_exception """

        logger.error('Error excution handler method(user:%s) details: %s'
                                  % (request.user, e), exc_info=True)


  