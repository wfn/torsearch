#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
import logging
import os
from logging import Formatter, FileHandler
from config import basedir

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={'autocommit': False, 'autoflush': False})
from torsearch import models # now we can import models which use the db we've just defined

debug_logger = logging.getLogger('torsearch')
debug_log_handler = FileHandler(os.path.join(basedir, 'debug.log'))
debug_log_formatter = Formatter('%(asctime)s %(levelname)s %(message)s '
'[in %(pathname)s:%(lineno)d]')
debug_log_handler.setFormatter(debug_log_formatter)
debug_logger.addHandler(debug_log_handler)
debug_logger.setLevel(logging.DEBUG)

if not app.debug:
  file_handler = FileHandler(os.path.join(basedir, 'error.log'))
  file_handler.setFormatter(debug_log_formatter)
  app.logger.setLevel(logging.INFO)
  file_handler.setLevel(logging.INFO)
  app.logger.addHandler(file_handler)
  app.logger.info('errors')

#init_db()

from torsearch import onionoo_api

@app.teardown_request
def teardown_request(exception):
  db.session.remove()

def init_db():
  db.create_all()

if __name__ == '__main__':
  pass
