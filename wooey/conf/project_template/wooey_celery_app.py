from __future__ import absolute_import

import os

from django.conf import settings

from celery import app as celery_app

app = celery_app.app_or_default()
# app = Celery('{{ project_name }}')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
