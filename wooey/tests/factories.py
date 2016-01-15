import factory
import os
import six
import uuid

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage

from ..models import WooeyJob, ScriptGroup, Script, ScriptParameter, ScriptParameterGroup, ScriptParameters

from .. import settings as wooey_settings


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


def generate_script(script_path):
    filename = os.path.split(script_path)[1]
    filename = os.path.join(wooey_settings.WOOEY_SCRIPT_DIR, filename)
    new_file = default_storage.save(filename, open(script_path))
    from ..backend import utils
    res = utils.add_wooey_script(script_path=new_file, group=None)
    return res['script']


def generate_job(script_version):
    return BaseJobFactory(script_version=script_version)
