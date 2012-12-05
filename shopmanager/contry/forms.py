from django import forms
from contry.models import Municipality,Location,County
from contry.widgets import MunicipalityChoiceWidget
from django.utils.translation import ugettext as _

class LocationForm(forms.ModelForm):
    name  = forms.CharField(max_length=20)
    county = forms.ModelChoiceField(queryset=County.objects.all())
    municipality = forms.ModelChoiceField(Municipality.objects.all(),
            widget=MunicipalityChoiceWidget(),
            label=_("Municipality"), required=False)

    class Meta:
        model = Location

    def __init__(self, *args, **kwargs):
        """
        We need access to the county field in the municipality widget, so we
        have to associate the form instance with the widget.
        """
        super(LocationForm, self).__init__(*args, **kwargs)
        self.fields['municipality'].widget.form_instance = self
