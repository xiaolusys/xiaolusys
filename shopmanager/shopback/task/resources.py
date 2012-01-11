from djangorestframework.resources import ModelResource
from shopback.task.models import ItemTask
from shopback.task.forms import ItemTaskForm


class ItemTaskResource(ModelResource):
    model = ItemTask
    form  = ItemTaskForm
    exclude = ('session_key',)


    def get_bound_form(self, data=None, files=None, method=None):
        form = super(ItemTaskResource, self).get_bound_form(data, files, method)
        session = self.view.request.session
        form.data['visitor_id'] = session['top_parameters']['visitor_id']
        form.data['visitor_nick'] = session['top_parameters']['visitor_nick']
        form.data['session_key'] = session.session_key

        form.data.pop('is_success',None)
        form.data.pop('status',None)

        return form
  