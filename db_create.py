# note: one is advised to use the db/db_create.sql raw SQL script instead.

from config import SQLALCHEMY_DATABASE_URI
from torsearch import db

db.create_all()
