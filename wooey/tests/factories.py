import factory
import os
import six

from django.contrib.auth import get_user_model

from ..models import WooeyJob, ScriptGroup, Script, ScriptParameter, ScriptParameterGroup, ScriptParameters

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
    script_path = factory.django.FileField(from_path=os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))


class ChoiceScriptFactory(ScriptFactory):
    script_path = factory.django.FileField(from_path=os.path.join(config.WOOEY_TEST_SCRIPTS, 'choices.py'))


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = 'user'
    email = 'a@a.com'
    password = 'testuser'


class BaseJobFactory(factory.DjangoModelFactory):
    class Meta:
        model = WooeyJob
    job_name = six.u('\xd0\xb9\xd1\x86\xd1\x83')
    job_description = six.u('\xd0\xb9\xd1\x86\xd1\x83\xd0\xb5\xd0\xba\xd0\xb5')


class TranslateJobFactory(BaseJobFactory):
    script = factory.SubFactory(TranslateScriptFactory)


class MultipleChoiceJobFactory(BaseJobFactory):
    script = factory.SubFactory(ChoiceScriptFactory)
