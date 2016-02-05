# coding: utf-8

from django import forms

class FormAttrs(object):
    pass


class BaseForm(forms.Form):
    # 如果验证成功则设置cleaned_attrs属性
    def clean(self):
        cleaned_data = super(BaseForm, self).clean()
        for k, v in self.initial.iteritems():
            if cleaned_data.get(k) != None:
                cleaned_data[k] = v
        for name in self.fields:
            initial_value = self.fields[name].initial
            if cleaned_data.get(name) == None and initial_value is not None:
                cleaned_data[name] = initial_value

        cleaned_attrs = FormAttrs()
        for k, v in cleaned_data.iteritems():
            setattr(cleaned_attrs, k, v)
        setattr(self, 'cleaned_attrs', cleaned_attrs)
        return cleaned_data
