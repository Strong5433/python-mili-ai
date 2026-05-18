from datetime import datetime

from sqlalchemy import DateTime, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_account: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    user_password: Mapped[str] = mapped_column(String(255), nullable=False)
    user_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    user_profile: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    user_role: Mapped[str] = mapped_column(String(32), nullable=False, default="user", server_default="user")
    edit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_delete: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
