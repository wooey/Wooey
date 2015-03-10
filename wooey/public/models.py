# -*- coding: utf-8 -*-
import datetime as dt
import json

from wooey.database import (
    Column,
    ReferenceCol,
    relationship,
    db,
    Model,
    SurrogatePK,
)

STATUS_WAITING = "W"
STATUS_RUNNING = "R"
STATUS_COMPLETE = "C"
STATUS_ERROR = "X"


class Script(SurrogatePK, Model):

    __tablename__ = 'scripts'
    name = Column(db.String(80), nullable=False)  # The basic name of the script
    display_name = Column(db.String(80), nullable=True)  # A nice, user friendly name

    exec_path = Column(db.String(255), unique=True, nullable=False)
    config_path = Column(db.String(255), unique=True, nullable=False)
    doc_path = Column(db.String(255), unique=True, nullable=True)

    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=db.func.now())

    description = Column(db.String(255), nullable=True)

    is_active = Column(db.Boolean(), default=True)

    def load_config(self):
        '''
        Load JSON config from file
        :return: dict of config
        '''

        with open(self.config_path, 'r') as f:
            return json.load(f)

    def load_docs(self):
        '''
        Load JSON config from file
        :return: dict of config
        '''
        if self.doc_path:
            with open(self.doc_path, 'r') as f:
                return f.read()
        else:
            return None


class Job(SurrogatePK, Model):

    __tablename__ = 'jobs'

    script_id = ReferenceCol('scripts')
    script = relationship('Script', backref='jobs')

    user_id = ReferenceCol('users')
    user = relationship('User', backref='jobs')

    path = Column(db.String(255), unique=True, nullable=False)

    created_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated_at = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=db.func.now())

    status = Column(db.Enum(STATUS_WAITING, STATUS_RUNNING, STATUS_COMPLETE, STATUS_ERROR), nullable=False, default=STATUS_WAITING)

    pid = Column(db.Integer, unique=False, nullable=True)

    config = Column(db.String(), nullable=True)

    @property
    def is_waiting(self):
        return self.status == STATUS_WAITING

    @property
    def is_running(self):
        return self.status == STATUS_RUNNING

    @property
    def is_complete(self):
        return self.status == STATUS_COMPLETE

    @property
    def is_error(self):
        return self.status == STATUS_ERROR
