Changelog
=========

v0.11.0
------------

| [`Feature
<https://github.com/wooey/Wooey/pull/175>`_] WooeyWidgets, which enable custom form input elements to be created and used.
| [`Feature
<https://github.com/wooey/Wooey/pull/254>`_] Korean translations added!
| [`Feature
<https://github.com/wooey/Wooey/pull/285>`_] Improved UI to not allow job operations on message brokers that do not allow them.
| [`Feature
<https://github.com/wooey/Wooey/pull/271>`_] Django2 Support.
| [`BugFix
<https://github.com/wooey/Wooey/pull/299>`_] Fix bug where all parameters from all subparsers were needed to validate in order to submit a job.
| [`BugFix
<https://github.com/wooey/Wooey/pull/296>`_] Fix bug with escaping parameter arguments that prevented special characters from being used.
| [`BugFix
<https://github.com/wooey/Wooey/pull/255>`_] Fix bug where multiple initial files for a cloned job were not populated.
| [`BugFix
<https://github.com/wooey/Wooey/pull/270>`_] Fix bug in parsing multiple arguments where argparse specifies `action='append'`
| [`BugFix
<https://github.com/wooey/Wooey/pull/277>`_] Fix bug in cleaning up empty jobs where workers cannot be contacted.
| [`BugFix
<https://github.com/wooey/Wooey/pull/145>`_] Fix bug where scripts on remote workers were not invalidated after updates on main server.
| [`BugFix
<https://github.com/wooey/Wooey/pull/297>`_] Fix race condition where celery tasks would start before database transaction finished.
| [`BugFix
<https://github.com/wooey/Wooey/pull/298>`_] Handle characters in script version that need to be escaped for urls.
