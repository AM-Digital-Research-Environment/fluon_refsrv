import sqlalchemy as sa
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import datetime

from ..db import Base

class User(Base):
    __tablename__  = 'user'
    id           :  Mapped[int]                 =   mapped_column(primary_key=True)
    name         :  Mapped[str]                 =   mapped_column(sa.String(255), unique=True)
    password     :  Mapped[str]                 =   mapped_column(sa.String(255), nullable=True)
    is_ldap_user :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    created_at   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())
    deleted_at   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=None, nullable=True)
    
    def __init__(self, name, password=None, is_ldap_user=False):
        self.name = name
        self.is_ldap_user = is_ldap_user
        self.password = password
        


