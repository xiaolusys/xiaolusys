from djangorestframework.views import ListOrCreateModelView as FrameworkListOrCreateModelView
from djangorestframework.views import ModelView ,ListModelView as FrameworkListModelView
from djangorestframework.views import InstanceModelView as FrameworkInstanceModelView
from djangorestframework.mixins import CreateModelMixin, InstanceMixin,ReadModelMixin
from djangorestframework import signals
from shopback.base.mixins import PaginatorMixin, CounterMixin, BatchGetMixin, DeleteModelMixin


class ListOrCreateModelView(PaginatorMixin, BatchGetMixin, FrameworkListOrCreateModelView):
    "Added Panigation function to ListOrCreateModelView"


class ListModelView(InstanceMixin,PaginatorMixin,BatchGetMixin,FrameworkListModelView):
    "Added Panigation function to ListModelView"


class SimpleListView(InstanceMixin,FrameworkListModelView):
    "docstring for view ListModelView"
    _suffix = 'List'


class CreateModelView(CreateModelMixin, ModelView):
    """A view which provides default operations for create, against a model in the database."""
    #_suffix = 'List'


class CounterModelView(CounterMixin, ModelView):
    """docstring for CounterModelView"""
    _suffix = 'List'


class InstanceModelView(DeleteModelMixin,FrameworkInstanceModelView):
    """docstring for InstanceModelView"""
    _suffix = 'Instance'


class SimpleInstanceView(InstanceMixin,ReadModelMixin,ModelView):
    "docstring for view ListModelView"
    _suffix = 'Instance'