import click
import flask.typing
from flask import current_app, g

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert

# ~ engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
engine = create_engine("postgresql://fo_services:fo_services@db/fo_services", echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

from .models import User, RecommUser, RecommItem

def fill_recomm_entity(sep=' '):
    entity_file = '/data/items_id.txt'
    with open(entity_file, 'r') as _in:
        header = _in.readline()
        logger.debug(header)
        header = header.strip().split(sep)
        id_idx = header.index('id')
        wid_idx = header.index('wisskiid')
        
        for line in _in:
            line = line.split(sep)
            _id  = int(line[id_idx])
            _wid = int(line[wid_idx])
            stmt = insert(RecommItem.__table__).values(wisski_id=_wid, recomm_id=_id).on_conflict_do_nothing()
            db_session.execute(stmt)
            db_session.commit()
    
            

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # ~ Base.metadata.drop_all(bind=engine)
    # ~ RecommItem.__table__.drop(engine)
    RecommUser.__table__.drop(engine)
    Base.metadata.create_all(bind=engine)
    # ~ fill_recomm_entity()

def get_user(username):
    try:
        u = db_session.query(User).filter(User.name==username).one()
        return u
    except:
        pass
    return None

def get_wisski_id_for_rec_id(rec_id):
    try:
        u = db_session.query(RecommItem).filter(RecommItem.recomm_id==rec_id).one()
        return u.wisski_id
    except:
        pass
    return None

def get_recomm_id_for_wisski_user(wisski_user):
    try:
        u = db_session.query(RecommUser).filter(RecommUser.wisski_id==wisski_user).one()
        return u.recomm_id
    except:
        logger.debug(f"couldn't find recommendation id for wisski user {wisski_user}")
        n_rows = db_session.query(RecommUser).count()
        if n_rows == 0:
            new_id = get_n_dummy_users() + 1 
        else:
            new_id = db_session.query(func.max(RecommUser.recomm_id)).scalar()
            new_id = new_id + 1
        new_user = RecommUser(wisski_user, new_id)
        db_session.add(new_user)
        db_session.commit()
        logger.debug(f"created mapping for wisski user {wisski_user}->{new_id}")
        return new_user.recomm_id
    return -1

def get_n_dummy_users():
    test_file = '/data/test.txt'
    count = 0
    with open(test_file, 'r') as _test:
        for count, _ in enumerate(_test):
            pass
    return count+1
