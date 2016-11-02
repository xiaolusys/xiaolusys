from django import forms


class ItemListTaskForm(forms.Form):
    user_id = forms.CharField(max_length=20)
    nick = forms.CharField(max_length=32)

    num_iid = forms.CharField(max_length=20)
    title = forms.CharField(max_length=128)
    num = forms.IntegerField(min_value=1)
    list_weekday = forms.IntegerField()
    list_time = forms.CharField(max_length=8)
    task_type = forms.CharField(max_length=10)
