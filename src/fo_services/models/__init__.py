import sqlalchemy as sa
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
import datetime

from ..db import Base


class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.String(255), unique=True)
    password: Mapped[str] = mapped_column(sa.String(255), nullable=True)
    is_ldap_user: Mapped[bool]
    created_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=sa.func.now()
    )
    deleted_at: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=None, nullable=True
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, is_ldap_user={self.is_ldap_user!r}, created_at={self.created_at!r}, deleted_at={self.deleted_at!r})"


class RecommUser(Base):
    __tablename__ = "rec_user"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wisski_id: Mapped[int] = mapped_column(unique=True, primary_key=True)
    first_seen: Mapped[datetime.datetime] = mapped_column(
        sa.DateTime, default=sa.func.now()
    )

    def __repr__(self) -> str:
        return f"RecommUser(id={self.id!r}, wisski_id={self.wisski_id!r}, first_seen={self.first_seen!r})"


class InteractionHistory(Base):
    __tablename__ = "hist_interact"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wisski_user: Mapped[int] = mapped_column(sa.ForeignKey("rec_user.wisski_id"))
    # wisski_item should not be foreign key relation, as new items may be added that have not been seen by the model yet
    wisski_item: Mapped[int]
    at: Mapped[datetime.datetime] = mapped_column(sa.DateTime, default=sa.func.now())

    def __repr__(self) -> str:
        return f"InteractionHistory(id={self.id!r}, wisski_user={self.wisski_user!r}, wisski_item={self.wisski_item!r}, at={self.at!r})"


class ItemClusterInfo(Base):
    __tablename__ = "item_cluster"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cluster: Mapped[int]
    rank: Mapped[int]
    # ~ among_top5   :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    # ~ among_top10  :  Mapped[bool]                =   mapped_column(unique=False, default=False)
    # ~ among_top50  :  Mapped[bool]                =   mapped_column(unique=False, default=False)

    def __repr__(self) -> str:
        return f"ItemClusterInfo(id={self.id!r}, cluster={self.cluster!r}, rank={self.rank!r})"


class UserRecommendationModel(Base):
    __tablename__ = "user_recommendation_model"
    user: Mapped[int] = mapped_column(primary_key=True)
    item: Mapped[int] = mapped_column(primary_key=True)
    rank: Mapped[int] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f"UserRecommendationModel(user={self.user!r}, item={self.item!r}, rank={self.rank!r})"


# ~ class RecommHistory(Base):
# ~ __tablename__  = 'hist_rec'
# ~ id           :  Mapped[int]                 =   mapped_column(primary_key=True,autoincrement=True)
# ~ wisski_id    :  Mapped[int]                 =   mapped_column(unique=True)
# ~ recomm_id    :  Mapped[int]                 =   mapped_column(unique=True)
# ~ first_seen   :  Mapped[datetime.datetime]   =   mapped_column(sa.DateTime, default=sa.func.now())

# ~ def __init__(self, wisski_id, recomm_id):
# ~ self.wisski_id = wisski_id
# ~ self.recomm_id = recomm_id
