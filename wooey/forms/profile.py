from django import forms


class APIKeyForm(forms.Form):
    name = forms.CharField()


class APIKeyIDForm(forms.Form):
    id = forms.IntegerField()
