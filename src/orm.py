import sqlalchemy.orm
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_login import UserMixin

class Base(DeclarativeBase):
    pass

class User(UserMixin, Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sqlalchemy.String(30))
    passphrase: Mapped[str] = mapped_column(sqlalchemy.String(50))

    is_admin: Mapped[bool] = mapped_column(default=False)
    password_hash: Mapped[str] =  mapped_column(sqlalchemy.String(64), nullable=True)