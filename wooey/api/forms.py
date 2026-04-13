from django import forms
from django.utils.translation import gettext_lazy as _

from .. import models


class SubmittedFieldsForm(forms.Form):
    def clean(self):
        cleaned_data = super(SubmittedFieldsForm, self).clean()
        return {
            field_name: value
            for field_name, value in cleaned_data.items()
            if field_name in self.data
        }


class SubmitForm(forms.Form):
    job_name = forms.CharField()
    job_description = forms.CharField(required=False)
    version = forms.CharField(required=False)
    iteration = forms.IntegerField(required=False)
    command = forms.CharField(required=False)


class ScriptMetadataForm(SubmittedFieldsForm):
    group = forms.CharField(required=False)
    virtual_environment = forms.ModelChoiceField(
        queryset=models.VirtualEnvironment.objects.order_by("name", "pk"),
        required=False,
    )
    script_description = forms.CharField(required=False)
    documentation = forms.CharField(required=False)
    script_order = forms.IntegerField(required=False, min_value=1)
    is_active = forms.NullBooleanField(required=False)
    ignore_bad_imports = forms.NullBooleanField(
        required=False,
        help_text=_(
            "Ignore bad imports when adding scripts. This is useful if a script is under a virtual environment."
        ),
    )
    execute_full_path = forms.NullBooleanField(required=False)
    save_path = forms.CharField(required=False)


class AddScriptForm(ScriptMetadataForm):
    default = forms.NullBooleanField(required=False)


class ScriptPatchForm(ScriptMetadataForm):
    script_name = forms.CharField(required=False)

    def clean_script_name(self):
        value = self.cleaned_data["script_name"]
        if "script_name" in self.data and not value.strip():
            raise forms.ValidationError(_("This field is required."))
        return value


class ScriptVersionPatchForm(SubmittedFieldsForm):
    default_version = forms.NullBooleanField(required=False)
    is_active = forms.NullBooleanField(required=False)

    def clean(self):
        cleaned_data = super(ScriptVersionPatchForm, self).clean()
        if "default_version" not in self.data and "is_active" not in self.data:
            raise forms.ValidationError(_("At least one field is required."))

        if (
            "default_version" in self.data
            and cleaned_data.get("default_version") is None
        ):
            self.add_error("default_version", _("This field is required."))

        if "is_active" in self.data and cleaned_data.get("is_active") is None:
            self.add_error("is_active", _("This field is required."))

        return cleaned_data


class VirtualEnvironmentFieldValidationMixin(object):
    def _clean_required_text_field(self, field_name):
        value = self.cleaned_data.get(field_name, "")
        if field_name in self.data and not value.strip():
            raise forms.ValidationError(_("This field is required."))
        return value

    def clean_name(self):
        return self._clean_required_text_field("name")

    def clean_python_binary(self):
        return self._clean_required_text_field("python_binary")

    def clean_venv_directory(self):
        return self._clean_required_text_field("venv_directory")


class VirtualEnvironmentCreateForm(VirtualEnvironmentFieldValidationMixin, forms.Form):
    name = forms.CharField(max_length=25)
    python_binary = forms.CharField(max_length=1024)
    requirements = forms.CharField(required=False)
    venv_directory = forms.CharField(max_length=1024)


class VirtualEnvironmentPatchForm(
    VirtualEnvironmentFieldValidationMixin, SubmittedFieldsForm
):
    name = forms.CharField(max_length=25, required=False)
    python_binary = forms.CharField(max_length=1024, required=False)
    requirements = forms.CharField(required=False)
    venv_directory = forms.CharField(max_length=1024, required=False)

    def clean(self):
        cleaned_data = super(VirtualEnvironmentPatchForm, self).clean()
        if not cleaned_data:
            raise forms.ValidationError(_("At least one field is required."))
        return cleaned_data
