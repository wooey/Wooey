from django import forms


class SubmitForm(forms.Form):
    job_name = forms.CharField()
    job_description = forms.CharField(required=False)
    version = forms.CharField(required=False)
    iteration = forms.IntegerField(required=False)
    command = forms.CharField(required=False)


class AddScriptForm(forms.Form):
    group = forms.CharField(required=False)
    default = forms.NullBooleanField(required=False)

    def clean_default(self):
        if self.cleaned_data["default"] is None:
            return True
        return self.cleaned_data["default"]
