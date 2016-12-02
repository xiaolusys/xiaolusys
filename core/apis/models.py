# coding: utf8
from __future__ import absolute_import, unicode_literals

import json

class DictObjectParseError(Exception):
    pass

class DictObject(dict):

    def __init__(self, id=None, **params):

        self._retrieve_params = params

        if id:
            self['id'] = id

    def _parse_objectable(self, adict):
        return 'object' in adict

    def fresh_form_data(self, object_dict):
        """Convert a dictionary to a class

        @param :adict Dictionary
        """
        if not self._parse_objectable(object_dict):
            raise DictObjectParseError('dict has no object entry!')

        for k, v in object_dict.items():
            if isinstance(v, dict) and self._parse_objectable(v):
                super(DictObject, self).__setitem__(k, DictObject().fresh_form_data(v))
            else:
                super(DictObject, self).__setitem__(k, v)

        return self

    def __str__(self):
        return json.dumps(self, sort_keys=False, indent=2)

    def __setattr__(self, k, v):
        if k[0] == '_' or k in self.__dict__:
            return super(DictObject, self).__setattr__(k, v)
        else:
            self[k] = v

    def __getattr__(self, k):
        if k[0] == '_':
            raise AttributeError(k)

        try:
            return self[k]
        except KeyError, err:
            raise AttributeError(*err.args)

    def __setitem__(self, k, v):
        # if v == "":
        #     raise ValueError(
        #         "You cannot set %s to an empty string. "
        #         "We interpret empty strings as None in requests."
        #         "You may set %s.%s = None to delete the property" % (
        #             k, str(self), k))

        super(DictObject, self).__setitem__(k, v)

    def __delitem__(self, k):
        raise TypeError(
            "You cannot delete attributes on a DictObject. "
            "To unset a property, set it to None.")