from django import forms
from django.forms import widgets
from django.forms.util import flatatt
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.contrib import admin
from django.utils.translation import ugettext as _

from contry.models import Municipality, Location

class MunicipalityChoiceWidget(widgets.Select):
    def render(self, name, value, attrs=None, choices=()):
        self.choices = [(u"", u"---------")]
        if value is None:
            # if no municipality has been previously selected,
            # render either an empty list or, if a county has
            # been selected, render its municipalities
            value = ''
            model_obj = self.form_instance.instance
            if model_obj and model_obj.county:
                for m in model_obj.county.municipality_set.all():
                    self.choices.append((m.id, smart_unicode(m)))
        else:
            # if a municipality X has been selected,
            # render only these municipalities, that belong
            # to X's county
            obj = Municipality.objects.get(id=value)
            for m in Municipality.objects.filter(county=obj.county):
                self.choices.append((m.id, smart_unicode(m)))

        # copy-paste from widgets.Select.render
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<select%s>' % flatatt(final_attrs)]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe(u'\n'.join(output))
