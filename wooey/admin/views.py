# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flask.ext.login import login_required, current_user

from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView


class AdminView(BaseView):

    def is_accessible(self):
        return current_user.is_authenticated() and current_user.is_admin

class ModelView(ModelView, AdminView):
    pass

from ..extensions import flask_admin, db
from ..user.models import User
from ..public.models import Script, Job

flask_admin.add_view(ModelView(User, db.session, endpoint='user-admin'))
flask_admin.add_view(ModelView(Script, db.session, endpoint='script-admin'))
flask_admin.add_view(ModelView(Job, db.session, endpoint='job-admin'))
