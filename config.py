import os

DEBUG = True

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = '<db_name>'
SQLALCHEMY_DATABASE_URI = 'postgres://<user>:<password>@localhost/' + DATABASE
COMMIT_AFTER = 10000 # max rows
BIND_HOST = '0.0.0.0' # careful now
BIND_PORT = 5555
