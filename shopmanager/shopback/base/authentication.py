from djangorestframework.authentication import BaseAuthentication


class UserLoggedInAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a :obj:`User` if the request session currently has a logged in user.
        Otherwise returns :const:`None`.
        """
        # TODO: Switch this back to request.POST, and let FormParser/MultiPartParser deal with the consequences.
        if getattr(request, 'user', None) and request.user.is_active:
            # If this is a POST request we enforce CSRF validation.
#            if request.method.upper() == 'POST':
#                # Temporarily replace request.POST with .DATA,
#                # so that we use our more generic request parsing
#                request._post = self.view.DATA
#                resp = CsrfViewMiddleware().process_view(request, None, (), {})
#                del(request._post)
#                if resp is not None:  # csrf failed
#                    return None
            return request.user
        return None