Changelog
=========

v0.14.0
-------

| [`Feature <https://github.com/wooey/Wooey/pull/383>`__] API Keys were added

v0.12.0
-------

| [`Feature <https://github.com/wooey/Wooey/pull/306>`__] Spanish Translations
| [`Feature <https://github.com/wooey/Wooey/pull/313>`__] Improve script deletion experience
| [`Feature <https://github.com/wooey/Wooey/pull/314>`__] Move from Appveyor and Travis to Github Actions
| [`Feature <https://github.com/wooey/Wooey/pull/284>`__] Add support for Django 2.2 and Django 3.0
| [`Feature <https://github.com/wooey/Wooey/commit/08bee7b8864a48d9cc8c54f25138bde6945f8451>`__] Add an official Docker Image
| [`Feature <https://github.com/wooey/Wooey/commit/6e4c3f92c6b1693b25576868c3f6773d1f9afdb5>`__] Add admin interface for Script Versions
| [`Debt <https://github.com/wooey/Wooey/pull/304>`__] Update to boto3

v0.11.0
------------

| [`Feature <https://github.com/wooey/Wooey/pull/175>`__] WooeyWidgets, which enable custom form input elements to be created and used.
| [`Feature <https://github.com/wooey/Wooey/pull/254>`__] Korean translations added!
| [`Feature <https://github.com/wooey/Wooey/pull/285>`__] Improved UI to not allow job operations on message brokers that do not allow them.
| [`Feature <https://github.com/wooey/Wooey/pull/271>`__] Django2 Support.
| [`BugFix <https://github.com/wooey/Wooey/pull/299>`__] Fix bug where all parameters from all subparsers were needed to validate in order to submit a job.
| [`BugFix <https://github.com/wooey/Wooey/pull/296>`__] Fix bug with escaping parameter arguments that prevented special characters from being used.
| [`BugFix <https://github.com/wooey/Wooey/pull/255>`__] Fix bug where multiple initial files for a cloned job were not populated.
| [`BugFix <https://github.com/wooey/Wooey/pull/270>`__] Fix bug in parsing multiple arguments where argparse specifies `action='append'`
| [`BugFix <https://github.com/wooey/Wooey/pull/277>`__] Fix bug in cleaning up empty jobs where workers cannot be contacted.
| [`BugFix <https://github.com/wooey/Wooey/pull/145>`__] Fix bug where scripts on remote workers were not invalidated after updates on main server.
| [`BugFix <https://github.com/wooey/Wooey/pull/297>`__] Fix race condition where celery tasks would start before database transaction finished.
| [`BugFix <https://github.com/wooey/Wooey/pull/298>`__] Handle characters in script version that need to be escaped for urls.
