from django import forms

__all__ = ["ScriptAdminForm"]


class ScriptAdminForm(forms.ModelForm):
    ignore_bad_imports = forms.BooleanField(required=False)
