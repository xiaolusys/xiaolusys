# from djangorestframework.resources import ModelResource
# from shopapp.autolist.models import ItemListTask
# from shopapp.autolist.forms import ItemListTaskForm
# 
# 
# class ItemListTaskResource(ModelResource):
#     model = ItemListTask
#     form  = ItemListTaskForm
#     exclude = ('status',)
# 
# 
#     def get_bound_form(self, data=None, files=None, method=None):
#         form = super(ItemListTaskResource, self).get_bound_form(data, files, method)
#         session = self.view.request.session
#         form.data['user_id'] = session['top_parameters']['visitor_id']
#         form.data['nick'] = session['top_parameters']['visitor_nick']
# 
#         return form
#
