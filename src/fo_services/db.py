import logging
import time
from collections.abc import Sequence
from typing import List, Tuple, TypedDict

import pandas as pd
from psycopg.errors import ForeignKeyViolation
from sqlalchemy import and_, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

logger = logging.getLogger(__name__)

# ~ engine = create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
engine = create_engine(
    "postgresql+psycopg://fo_services:fo_services@db/fo_services", echo=True
)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


class Base(DeclarativeBase):
    pass


Base.query = db_session.query_property()

from .models import (
    InteractionHistory,
    ItemClusterInfo,
    RecommUser,
    User,
    UserRecommendationModel,
)


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    # ~ Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def get_user(username):
    try:
        u = db_session.query(User).filter(User.name == username).one()
        return u
    except Exception:
        logger.exception("Error fetching user")

    return None


def is_new_user(wisski_user_id: int) -> bool:
    is_new = True

    try:
        db_session.query(RecommUser.wisski_id).filter(
            RecommUser.wisski_id == wisski_user_id
        ).one()
        is_new = False
    except Exception:
        pass

    if not is_new:
        try:
            logger.debug(f"looking for recommendations for {wisski_user_id}")
            db_session.query(UserRecommendationModel.user).filter(
                UserRecommendationModel.user == wisski_user_id
            ).all()
            logger.debug(f"found recommendations for {wisski_user_id}")
        except Exception:
            is_new = True
    else:
        try:
            db_session.add(RecommUser(wisski_id=wisski_user_id))
            db_session.commit()
            logger.debug(f"added new user {wisski_user_id}")
        except Exception:
            logger.exception("Error creating new user")
            db_session.rollback()

    return is_new


def get_itemlist_from_model(user_id: int, max_n: int) -> List[Tuple[int, int, int]]:
    rows = (
        db_session.query(UserRecommendationModel, ItemClusterInfo)
        .filter(UserRecommendationModel.user == user_id)
        .filter(UserRecommendationModel.item == ItemClusterInfo.id)
        .order_by(UserRecommendationModel.rank.asc())
        .limit(max_n)
        .all()
    )
    return [(row[0].item, row[0].rank, row[1].cluster) for row in rows]


def get_itemlist_from_cluster(top_n: int) -> List[Tuple[int, int, int]]:
    rows = (
        db_session.query(
            ItemClusterInfo.id, ItemClusterInfo.rank, ItemClusterInfo.cluster
        )
        .filter(and_(ItemClusterInfo.cluster != -1, ItemClusterInfo.rank < top_n))
        .order_by(ItemClusterInfo.rank)
        .all()
    )

    return [(row.id, row.rank, row.cluster) for row in rows]


def log_user_detail_interaction(wisski_user: int, wisski_item: int):
    try:
        db_session.add(RecommUser(wisski_id=wisski_user))
        db_session.commit()
    except Exception:
        db_session.rollback()

    try:
        db_session.add(
            InteractionHistory(wisski_user=wisski_user, wisski_item=wisski_item)
        )
        db_session.commit()
        return True
    except Exception:
        logger.exception("error in logging interaction history: ")
        db_session.rollback()

    return False


def export_user_data(known_users_file):
    data = pd.read_sql_query(
        select(RecommUser.wisski_id, RecommUser.first_seen), engine
    )
    data.to_csv(known_users_file, index=False, sep="\t")


def export_interaction_data(interaction_history_file):
    data = pd.read_sql_query(
        select(
            InteractionHistory.wisski_user,
            InteractionHistory.wisski_item,
            InteractionHistory.at,
        ),
        engine,
    )
    data.to_csv(interaction_history_file, index=False, sep="\t")


class UpdateModelResult(TypedDict):
    cluster_assignments_to_write: int
    cluster_assignments_written: int
    reco_assignments_written: int
    reco_assignments_to_write: int
    elapsed: float


def update_model_infos(
    cluster_data: Sequence, recommendation_data: Sequence
) -> UpdateModelResult:
    logger.debug("updating model infos")
    start = time.time()

    try:
        # must come first due to foreign key relations to ItemClusterInfo
        db_session.query(UserRecommendationModel).delete()
        db_session.query(ItemClusterInfo).delete()
        db_session.commit()
    except Exception:
        db_session.rollback()
        logger.exception("Error truncating tables prior to update")
        return UpdateModelResult(
            cluster_assignments_to_write=len(cluster_data),
            cluster_assignments_written=0,
            reco_assignments_to_write=len(recommendation_data),
            reco_assignments_written=0,
            elapsed=time.time() - start,
        )

    # try is outside the loop as insertion shouldn't fail for single items
    with db_session.begin():
        for item in cluster_data:
            db_session.add(
                ItemClusterInfo(
                    id=item["id"], cluster=item["cluster"], rank=item["rank"]
                )
            )

    # try inside loop, as inserting a single row can violate foreign key constraints, in which case we want to simply continue
    for item in recommendation_data:
        db_session.add(
            UserRecommendationModel(
                user=item["user"], item=item["item"], rank=item["rank"]
            )
        )
        try:
            db_session.commit()
        except (IntegrityError, ForeignKeyViolation):
            db_session.rollback()
            logger.exception("Integrity error inserting user-reco. Rolling back.")

    n_rows_cluster = db_session.query(ItemClusterInfo).count()
    logger.info(f"read {n_rows_cluster} items to {ItemClusterInfo.__tablename__}")

    n_rows_recos = db_session.query(UserRecommendationModel).count()
    logger.info(f"read {n_rows_recos} items to {UserRecommendationModel.__tablename__}")

    return UpdateModelResult(
        cluster_assignments_to_write=len(cluster_data),
        cluster_assignments_written=n_rows_cluster,
        reco_assignments_to_write=len(recommendation_data),
        reco_assignments_written=n_rows_recos,
        elapsed=time.time() - start,
    )
