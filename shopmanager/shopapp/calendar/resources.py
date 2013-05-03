from djangorestframework.resources import ModelResource


class MainStaffEventResource(ModelResource):
    """ docstring for MainStaffEventResource """

    fields = ('curuser','staffs',)
    exclude = ('url',) 