from django.test import TestCase

from . import factories


class ScriptTestCase(TestCase):

    def test_script_creation(self):
        script = factories.TranslateScriptFactory()


class ScriptGroupTestCase(TestCase):

    def test_script_group_creation(self):
        group = factories.ScriptGroupFactory()