from __future__ import absolute_import

__author__ = 'chris'
from django.forms import CharField, FileField, FilePathField, widgets


class WooeyOutputFileField(FileField):
    widget = widgets.TextInput

    def __init__(self, *args, **kwargs):
        kwargs['allow_empty_file'] = True
        super().__init__(*args, **kwargs)


# TODO: Make a complex widget of filepathfield/filefield
class WooeyUploadFileField(FileField):
    pass
