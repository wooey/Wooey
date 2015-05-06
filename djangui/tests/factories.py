import factory
import os

from ..models import DjanguiJob, ScriptGroup, Script, ScriptParameter, ScriptParameterGroup, ScriptParameters

from . import config



class ScriptGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = ScriptGroup

    group_name = 'test group'
    group_description = 'test desc'

class ScriptFactory(factory.DjangoModelFactory):
    class Meta:
        model = Script

    script_name = 'test script'
    script_group = factory.SubFactory(ScriptGroupFactory)
    script_description = 'test script desc'

class TranslateScriptFactory(ScriptFactory):

    script_path = factory.django.FileField(from_path=os.path.join(config.DJANGUI_TEST_SCRIPTS, 'translate.py'))