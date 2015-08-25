from __future__ import absolute_import
__author__ = 'chris'

import json

from django.forms import CharField, FileField, FilePathField, FileInput
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy


class WooeyOutputFileField(FileField):
    widget = widgets.TextInput

    def __init__(self, *args, **kwargs):
        kwargs['allow_empty_file'] = True
        super(WooeyOutputFileField, self).__init__(*args, **kwargs)


# TODO: Make a complex widget of filepathfield/filefield
class WooeyUploadFileField(FileField):
    pass

class WooeyFileInput(FileInput):
    """
        Initial data is a dictionary of folders/files to display
    """
    initial_text = ugettext_lazy('Files Available')
    input_text = ugettext_lazy('Upload')
    load_jtree_text = ugettext_lazy('View Files')
    clear_tree_label = ugettext_lazy('Clear Tree')
    tree_plugins = '["checkbox"]'

    template = (
        '<div id="%(tree_id)s"></div>'
        '<input id="%(tree_input)s" type="hidden"/>'
        '<button class="btn btn-primary btn-sm jtree-load" data-src="%(jtree_data_source)s">%(load_jtree_text)s</button>'
        '<script>'
        '$(".jtree-load").click(function(event){'
        '   event.preventDefault();'
        '   $("#%(tree_id)s").jstree({'
        '       "core": {'
        '           "data": {'
        '               "url": $(this).data("src")'
        '               }'
        '           },'
        '       "plugins": ["state", "search", "checkbox"]'
        '   });'
        '});'
        '</script>'
        '<br />%(input_text)s: %(input)s'
    )

    template_with_initial = (
        '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )

    template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'

    def tree_id(self, name):
        """
        Given the name of the file input, return the name of the clear checkbox
        input.
        """
        return name + '_tree_id'

    def tree_input(self, name):
        """
        Given the name of the file input, return the name of the clear checkbox
        input.
        """
        return name + '_tree_input_id'

    def is_initial(self, value):
        """
        Return whether value is considered to be initial value.
        """
        return value

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_tree_label,
        }
        template = '%(input)s'
        substitutions['input'] = super(WooeyFileInput, self).render(name, value, attrs)

        if self.is_initial(value):
            template = self.template
            # substitutions.update(self.get_template_substitution_values(value))
            substitutions['tree_id'] = self.tree_id(name)
            substitutions['tree_input'] = self.tree_input(name)
            substitutions['tree_plugins'] = self.tree_plugins
            substitutions['load_jtree_text'] = self.load_jtree_text
            substitutions['jtree_data_source'] = value
        return mark_safe(template % substitutions)

    def value_from_datadict(self, data, files, name):
        upload = super(WooeyFileInput, self).value_from_datadict(data, files, name)
        if not self.is_required:
            if upload:
                pass
                # If the user contradicts themselves (uploads a new file AND
                # checks the "clear" checkbox), we return a unique marker
                # object that FileField will turn into a ValidationError.
                # return FILE_INPUT_CONTRADICTION
            # False signals to clear any existing value, as opposed to just None
            return False
        return upload
