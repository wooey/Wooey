import os
import six
import zipfile

from django.test import TestCase

from ..backend import utils

from . import factories
from . import config
from . import mixins


class TestUtils(mixins.ScriptFactoryMixin, mixins.FileMixin, TestCase):
    def test_sanitize_name(self):
        assert(utils.sanitize_name('abc')) == 'abc'
        assert(utils.sanitize_name('ab c')) == 'ab_c'
        assert(utils.sanitize_name('ab-c')) == 'ab_c'

    def test_sanitize_string(self):
        assert(utils.sanitize_string('ab"c')) == 'ab\\"c'

    def test_add_script(self):
        pass
        # TODO: fix me
        # utils.add_wooey_script(script=os.path.join(config.WOOEY_TEST_SCRIPTS, 'translate.py'))

    def test_anonymous_users(self):
        from .. import settings as wooey_settings
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        wooey_settings.WOOEY_ALLOW_ANONYMOUS = False
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])

    def test_valid_user(self):
        user = factories.UserFactory()
        script_version = self.translate_script
        script = script_version.script
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])
        from .. import settings as wooey_settings
        self.assertEqual('disabled', d['display'])
        wooey_settings.WOOEY_SHOW_LOCKED_SCRIPTS = False
        d = utils.valid_user(script, user)
        self.assertEqual('hide', d['display'])
        from django.contrib.auth.models import Group
        test_group = Group(name='test')
        test_group.save()
        script.user_groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertFalse(d['valid'])
        user.groups.add(test_group)
        d = utils.valid_user(script, user)
        self.assertTrue(d['valid'])

    def test_job_file_outputs(self):
        # Run a script that creates a file
        from wooey.models import WooeyJob, UserFile
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'file_maker.py')
        with open(script) as o:
            new_file = self.storage.save(self.filename_func('file_maker.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        job = utils.create_wooey_job(
            script_version_pk=res['script'].pk,
            data={'job_name': 'abc'}
        )
        # Get the new job
        job.submit_to_celery()
        job = WooeyJob.objects.get(pk=job.pk)
        utils.create_job_fileinfo(job)

        # Make sure the file info is correct
        self.assertEqual(UserFile.objects.filter(job=job).count(), 4)
        for job_file in UserFile.objects.filter(job=job):
            wooey_file = job_file.system_file
            self.assertEqual(
                os.path.getsize(self.storage.path(wooey_file.filepath.name)),
                wooey_file.size_bytes,
            )

        # Check for the zip file overwrite in for https://github.com/wooey/Wooey/issues/202
        zip_file = UserFile.objects.get(job=job, filename__endswith='zip')
        _zip = zipfile.ZipFile(zip_file.system_file.filepath)
        files = [filename.filename for filename in _zip.filelist]
        six.assertCountEqual(self, files, ['abc/', 'abc/test_file', 'abc/test_dir/test_file'])

    def test_add_wooey_script(self):
        from wooey.models import ScriptParser
        script = os.path.join(config.WOOEY_TEST_SCRIPTS, 'file_maker.py')
        with open(script) as o:
            new_file = self.storage.save(self.filename_func('file_maker.py'), o)
        res = utils.add_wooey_script(script_path=new_file, group=None)
        self.assertEqual(res['valid'], True, res['errors'])
        parser = ScriptParser.objects.get(script_version=res['script'])
        self.assertEqual(parser.name, u'')

class TestFileDetectors(TestCase):
    def test_detector(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'fasta.fasta')
        res, preview = utils.test_fastx(self.file)
        self.assertEqual(res, True, 'Fastx parser fail')
        self.assertEqual(preview, open(self.file).readlines(), 'Fastx Preview Fail')

    def test_delimited(self):
        self.file = os.path.join(config.WOOEY_TEST_DATA, 'delimited.tsv')
        res, preview = utils.test_delimited(self.file)
        self.assertEqual(res, True, 'Delimited parser fail')
        self.assertEqual(preview, [i.strip().split('\t') for i in open(self.file).readlines()], 'Delimited Preview Fail')
