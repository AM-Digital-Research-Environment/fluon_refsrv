import click
import flask.typing
from flask import current_app, g

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoResultFound

# ~ engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
engine = create_engine("postgresql://fo_services:fo_services@db/fo_services", echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from .db_models import User
    # ~ Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def get_user(username):
    from .db_models import User
    try:
        u = db_session.query(User).filter(User.name==username).one()
        return u
    except NoResultFound:
        return None
