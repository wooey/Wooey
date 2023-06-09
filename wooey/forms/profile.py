from django import forms


class APIKeyForm(forms.Form):
    name = forms.CharField()
