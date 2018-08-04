import factory
import six
from django.contrib.auth import get_user_model

from ..models import Script, ScriptGroup, WooeyJob, WooeyWidget
from . import utils as test_utils


class ScriptGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = ScriptGroup

    group_name = 'test group'
    group_description = 'test desc'


class ScriptParameterGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'wooey.ScriptParameterGroup'


class ScriptParameterFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'wooey.ScriptParameter'

    script_param = 'script-param'
    is_output = False
    parameter_group = factory.SubFactory('wooey.tests.factories.ScriptParameterGroupFactory')
    parser = factory.SubFactory('wooey.tests.factories.ScriptParserFactory')


class ScriptParserFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'wooey.ScriptParser'


class ScriptFactory(factory.DjangoModelFactory):
    class Meta:
        model = Script

    script_name = 'test script'
    script_group = factory.SubFactory(ScriptGroupFactory)
    script_description = 'test script desc'


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


class WooeyWidgetFactory(factory.DjangoModelFactory):
    class Meta:
        model = WooeyWidget

    name = 'test widget'


def generate_script(script_path, script_name=None):
    new_file = test_utils.save_script_path(script_path)
    from ..backend import utils
    res = utils.add_wooey_script(script_name=script_name, script_path=new_file, group=None)
    return res['script']


def generate_job(script_version):
    return BaseJobFactory(script_version=script_version)
