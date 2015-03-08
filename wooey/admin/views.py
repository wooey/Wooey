# -*- coding: utf-8 -*-
from flask import Blueprint, render_template
from flask.ext.login import login_required
from flask.ext import login

from flask.ext.admin import Admin, BaseView, expose
from flask.ext.admin.contrib.sqla import ModelView


class AdminView(BaseView):

    def is_accessible(self):
        return login.current_user.is_authenticated()

    @expose('/')
    def index(self):
        return self.render('index.html')

from ..extensions import flask_admin, db

from ..user.models import User
flask_admin.add_view(ModelView(User, db.session, endpoint='user-admin'))

from ..public.models import Script, Job
flask_admin.add_view(ModelView(Script, db.session, endpoint='script-admin'))
flask_admin.add_view(ModelView(Job, db.session, endpoint='job-admin'))
