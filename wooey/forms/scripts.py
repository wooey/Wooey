from __future__ import absolute_import
from django import forms


class WooeyForm(forms.Form):

    def add_wooey_fields(self):
        # This adds fields such as job name, description that we like to validate on but don't want to include in
        # form rendering
        self.fields['job_name'] = forms.CharField()
        self.fields['job_description'] = forms.CharField(required=False)
