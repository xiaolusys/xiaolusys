from django import forms

class AdminTextThumbnailWidget(forms.TextInput):

    def render(self, name, value, attrs=None):
       #not quite sure what is in `value`, I've not been so far
       return '<img src="%s" style="width:%dpx;height:%dpx;"/>' % (value or '',
            attrs.get('width',80), attrs.get('height',80))
