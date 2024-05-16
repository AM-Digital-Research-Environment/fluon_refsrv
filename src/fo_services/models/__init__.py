import sqlalchemy as sa
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import datetime

from ..db import Base


class User(Base):
    __tablename__  = 'user'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True,autoincrement=True)
    name         :  Mapped[str]                 =   mapped_column(sa.String(255), unique=True)
    password     :  Mapped[str]                 =   mapped_column(sa.String(255), nullable=True)
    is_ldap_user :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    created_at   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    deleted_at   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=None, nullable=True)
    
    def __init__(self, name, password=None, is_ldap_user=False):
        self.name = name
        self.is_ldap_user = is_ldap_user
        self.password = password


class RecommUser(Base):
    __tablename__  = 'rec_user'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True,autoincrement=True)
    wisski_id    :  Mapped[int]                 =   mapped_column(unique=True, primary_key=True)
    first_seen   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    def __init__(self, wisski_id):
        self.wisski_id = wisski_id


class InteractionHistory(Base):
    __tablename__  = 'hist_interact'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True, autoincrement=True)
    wisski_user  :  Mapped[int]                 =   mapped_column(sa.ForeignKey('rec_user.wisski_id'))
    wisski_item  :  Mapped[int]                 =   mapped_column() # das darf kein foreign key sein, da items hinzu kommen können, die noch nicht ins modell eingeflossen sind
    at           :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    def __init__(self, wisski_user, wisski_item):
        self.wisski_user = wisski_user
        self.wisski_item = wisski_item


class ItemClusterInfo(Base):
    __tablename__ = 'item_cluster'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True, autoincrement=True)
    cluster      :  Mapped[int]                 =   mapped_column(primary_key=False, autoincrement=False)
    rank         :  Mapped[int]                 =   mapped_column(primary_key=False, autoincrement=False)
    # ~ among_top5   :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    # ~ among_top10  :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    # ~ among_top50  :  Mapped[bool]                =   mapped_column(unique=False, default=False)

    def __init__(self, _id, _cls, _rnk):
        self.id = _id
        self.cluster = _cls
        self.rank = _rnk
        # ~ self.among_top5 = _rnk < 5
        # ~ self.among_top10 = _rnk < 10
        # ~ self.among_top50 = _rnk < 50


class UserRecommendationModel(Base):
    __tablename__ = 'user_recommendation_model'
    user         :  Mapped[int]                 =   mapped_column(sa.ForeignKey('rec_user.wisski_id'), primary_key=True)
    item         :  Mapped[int]                 =   mapped_column(sa.ForeignKey('item_cluster.id'), primary_key=True)
    rank         :  Mapped[int]                 =   mapped_column()

# ~ class RecommHistory(Base):
    # ~ __tablename__  = 'hist_rec'
    # ~ id           :  Mapped[int]                 =   mapped_column(primary_key=True,autoincrement=True)
    # ~ wisski_id    :  Mapped[int]                 =   mapped_column(unique=True)
    # ~ recomm_id    :  Mapped[int]                 =   mapped_column(unique=True)
    # ~ first_seen   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    # ~ def __init__(self, wisski_id, recomm_id):
        # ~ self.wisski_id = wisski_id
        # ~ self.recomm_id = recomm_id
   
