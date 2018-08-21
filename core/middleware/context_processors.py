from django.contrib.messages.api import get_messages


def session(request):
    """
    Returns a lazy 'messages' context variable.
    """
    session_key = request.session.cache_key
    if session_key:
        session_key = session_key[-32:]
    return {'sessionid':session_key }