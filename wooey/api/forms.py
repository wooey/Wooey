from django import forms
from django.utils.translation import gettext_lazy as _


class SubmitForm(forms.Form):
    job_name = forms.CharField()
    job_description = forms.CharField(required=False)
    version = forms.CharField(required=False)
    iteration = forms.IntegerField(required=False)
    command = forms.CharField(required=False)


class AddScriptForm(forms.Form):
    group = forms.CharField(required=False)
    default = forms.NullBooleanField(required=False)
    ignore_bad_imports = forms.BooleanField(
        required=False,
        help_text=_(
            "Ignore bad imports when adding scripts. This is useful if a script is under a virtual environment."
        ),
    )

    def clean_default(self):
        if self.cleaned_data["default"] is None:
            return True
        return self.cleaned_data["default"]

    def clean_ignore_bad_imports(self):
        if self.cleaned_data["ignore_bad_imports"] is None:
            return False
        return self.cleaned_data["ignore_bad_imports"]
