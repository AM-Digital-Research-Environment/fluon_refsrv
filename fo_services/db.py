import click
import flask.typing
from flask import current_app, g

import logging
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, func, select, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import NoResultFound
from sqlalchemy.dialects.postgresql import insert

import pandas as pd

# ~ engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
engine = create_engine("postgresql://fo_services:fo_services@db/fo_services", echo=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

from .models import *

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # ~ Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    

def get_user(username):
    try:
        u = db_session.query(User).filter(User.name==username).one()
        return u
    except:
        pass
    return None


def is_new_user(wisski_user):
    is_new = True
    try:
        db_session.query(RecommUser.wisski_id).filter(RecommUser.wisski_id==wisski_user).one()
        is_new = False
    except:
        pass
    if not is_new:
        try:
            logger.debug(f"looking for recommendations for {wisski_user}")
            db_session.query(UserRecommendationModel.user).filter(UserRecommendationModel.user == wisski_user).all()
            logger.debug(f"found recommendations for {wisski_user}")
        except:
            is_new = True
    else:
        db_session.add(RecommUser(wisski_user))
        db_session.commit()
        logger.debug(f"added new user {wisski_user}")
    return is_new

def get_itemlist_from_model(user_id,max_n):
    rows = db_session.query(UserRecommendationModel,ItemClusterInfo).filter(UserRecommendationModel.user==user_id).filter(UserRecommendationModel.item == ItemClusterInfo.id).order_by(UserRecommendationModel.rank.asc()).limit(max_n).all()
    return [(row[0].item, row[0].rank, row[1].cluster) for row in rows]
    
def get_itemlist_from_cluster(top_n):
    
    rows = db_session.query(ItemClusterInfo.id,ItemClusterInfo.rank,ItemClusterInfo.cluster).filter(and_(ItemClusterInfo.cluster != -1, ItemClusterInfo.rank < top_n)).order_by(ItemClusterInfo.rank).all()
    
    return [(row.id, row.rank, row.cluster) for row in rows]

def log_user_detail_interaction(wisski_user, wisski_item):
    try:
        db_session.add(InteractionHistory(int(wisski_user), int(wisski_item)))
        db_session.commit()
        return True
    except Exception as e:
        logger.debug("error in logging interaction history: "+repr(e))
        pass
    return False

def export_user_data(known_users_file):
    data = pd.read_sql_query(select(RecommUser.wisski_id, RecommUser.first_seen), engine)
    data.to_csv(known_users_file, index=False, sep='\t')
    
def export_interaction_data(interaction_history_file):
    data = pd.read_sql_query(select(InteractionHistory.wisski_user,InteractionHistory.wisski_item,InteractionHistory.at), engine)
    data.to_csv(interaction_history_file, index=False, sep='\t')
 

def update_model_infos(cluster_data, recommendation_data):
    logger.debug("updating model infos")
    
    try:
        UserRecommendationModel.query.delete()
        db_session.commit()
    except:
        pass
    try:
        ItemClusterInfo.query.delete()
        db_session.commit()
    except:
        pass
    
    # ~ try:
        # ~ UserRecommendationModel.__table__.drop(engine)
        # ~ ItemClusterInfo.__table__.drop(engine)
    # ~ except:
        # ~ pass
    # ~ Base.metadata.create_all(bind=engine)
    
    conn = engine.raw_connection()
    
    # ~ try:
    with conn.cursor() as cur, open(cluster_data, 'r') as _f:
        header = _f.readline()
        if not header.startswith('#'):
            _f.seek(0)
        # https://www.psycopg.org/docs/cursor.html#cursor.copy_from
        cur.copy_from(
            _f,
            ItemClusterInfo.__tablename__,  # table name
            sep=' ',
            columns=('id', 'cluster', 'rank'),
        )
    conn.commit()
    n_rows = db_session.query(ItemClusterInfo).count()
    logger.info(f"read {n_rows} items to {ItemClusterInfo.__tablename__}")
    
    with conn.cursor() as cur, open(recommendation_data, 'r') as _f:
        header = _f.readline()
        if not header.startswith('#'):
            _f.seek(0)
        cur.copy_from(
            _f,
            UserRecommendationModel.__tablename__,  # table name
            sep=' ',
            columns=('user', 'item', 'rank'),
        )
    conn.commit()
    n_rows = db_session.query(UserRecommendationModel).count()
    logger.info(f"read {n_rows} items to {UserRecommendationModel.__tablename__}")
    # ~ except:
        # ~ db_session.rollback()
        # ~ return False
    
    return True
