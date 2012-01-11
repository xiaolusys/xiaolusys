from django import forms


class ItemTaskForm(forms.Form):

    visitor_id = forms.CharField(max_length=20)
    visitor_nick = forms.CharField(max_length=32)
    session_key = forms.CharField(max_length=32)

    num_iid = forms.CharField(max_length=20)
    title = forms.CharField(max_length=128)
    num = forms.IntegerField(min_value=1)
    update_time = forms.DateTimeField()
    task_type = forms.IntegerField(min_value=1,max_value=2)


  