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
    recomm_id    :  Mapped[int]                 =   mapped_column(unique=True, primary_key=True)
    first_seen   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    def __init__(self, wisski_id, recomm_id):
        self.wisski_id = wisski_id
        self.recomm_id = recomm_id
        

class RecommItem(Base):
    __tablename__  = 'rec_entity'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True, autoincrement=True)
    wisski_id    :  Mapped[int]                 =   mapped_column(unique=True, primary_key=True)
    recomm_id    :  Mapped[int]                 =   mapped_column(unique=True, primary_key=True)
    
    def __init__(self, wisski_id, recomm_id):
        self.wisski_id = wisski_id
        self.recomm_id = recomm_id


class InteractionHistory(Base):
    __tablename__  = 'hist_interact'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True, autoincrement=True)
    wisski_user  :  Mapped[int]                 =   mapped_column(unique=False, primary_key=False)
    wisski_item  :  Mapped[int]                 =   mapped_column(unique=False, primary_key=False)
    at           :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    def __init__(self, wisski_user, wisski_item):
        self.wisski_user = wisski_user
        self.wisski_item = wisski_item


# ~ class RecommHistory(Base):
    # ~ __tablename__  = 'hist_rec'
    # ~ id           :  Mapped[int]                 =   mapped_column(primary_key=True,autoincrement=True)
    # ~ wisski_id    :  Mapped[int]                 =   mapped_column(unique=True)
    # ~ recomm_id    :  Mapped[int]                 =   mapped_column(unique=True)
    # ~ first_seen   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    
    # ~ def __init__(self, wisski_id, recomm_id):
        # ~ self.wisski_id = wisski_id
        # ~ self.recomm_id = recomm_id
   
