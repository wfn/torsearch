from config import SQLALCHEMY_DATABASE_URI
from torsearch import db

db.create_all()
