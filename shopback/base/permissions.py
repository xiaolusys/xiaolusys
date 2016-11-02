# from djangorestframework.permissions import BasePermission,  IsAuthenticated, PerUserThrottling, PerViewThrottling, PerResourceThrottling, _403_FORBIDDEN_RESPONSE
# 
# import logging
# logger = logging.getLogger('django.request')
# 
# class OwnsObjPermission(BasePermission):
#     """docstring for OwnsObjPermission"""
#     def check_permission(self, user, obj=None):
#         uid = getattr(obj, 'uid', None)
#         if uid and uid != user.get_profile().uid:
#             raise _403_FORBIDDEN_RESPONSE
# 
# 
# class CommentUserPermission(BasePermission):
#     """docstring for OwnsObjPermission"""
#     def check_permission(self, user, obj=None):
#         method = self.view.method.upper()
#         if method == 'POST':
#             user_id = self.view.request.POST.get('user_id',None)
#             if not user_id:
#                 raise _403_FORBIDDEN_RESPONSE
#             from evaluate.users.models import User
# 
#             try:
#                 User.objects.get(pk=user_id)
#             except :
#                 raise _403_FORBIDDEN_RESPONSE
# 
# 
#
