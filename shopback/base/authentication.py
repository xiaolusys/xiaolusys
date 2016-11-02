# from djangorestframework.authentication import BaseAuthentication
from rest_framework import authentication
from django.http import HttpResponse, HttpResponseNotFound


# class UserLoggedInAuthentication(authentication):
#     """
#     Use Django's session framework for authentication.
#     """
#  
#     def authenticate(self, request):
#         """
#         Returns a :obj:`User` if the request session currently has a logged in user.
#         Otherwise returns :const:`None`.
#         """
#         # TODO: Switch this back to request.POST, and let FormParser/MultiPartParser deal with the consequences.
#         if getattr(request, 'user', None) and request.user.is_active:
#             # If this is a POST request we enforce CSRF validation.
# #            if request.method.upper() == 'POST':
# #                # Temporarily replace request.POST with .DATA,
# #                # so that we use our more generic request parsing
# #                request._post = self.view.DATA
# #                resp = CsrfViewMiddleware().process_view(request, None, (), {})
# #                del(request._post)
# #                if resp is not None:  # csrf failed
# #                    return None
#             return request.user
#         return None


def login_required_ajax(function=None, redirect_field_name=None):
    # from djangorestframework.authentication import BaseAuthentication
    """
    Just make sure the user is authenticated to access a certain ajax view
 
    Otherwise return a HttpResponse 401 - authentication required
    instead of the 302 redirect of the original Django decorator
    """

    def _decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)

        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)
