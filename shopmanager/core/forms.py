# coding: utf-8
__author__ = 'yan.huang'

from django import forms


class FormAttrs(object):
    pass


class BaseForm(forms.Form):
    def clean(self):
        """
            # 如果验证成功则设置cleaned_attrs属性
            恩俊写的，不习惯cleaned_data的字典形式，想改成属性形式 并无别的提升
        """
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

    @property
    def error_message(self):
        # todo@hy 应该是as_json然后把key转化成verbose_name
        return self.errors.as_text()


class ModelField(forms.Field):
    pass