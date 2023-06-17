from django import forms


class SubmitForm(forms.Form):
    job_name = forms.CharField()
    version = forms.CharField(required=False)
    iteration = forms.IntegerField(required=False)
    command = forms.CharField(required=False)


class AddScriptForm(forms.Form):
    group = forms.CharField(required=False)
