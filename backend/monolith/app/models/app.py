from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class App(Base):
    __tablename__ = "app"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    app_name: Mapped[str] = mapped_column(String(128), nullable=False, default="My App", server_default="My App")
    cover: Mapped[str | None] = mapped_column(String(512), nullable=True)
    init_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    code_gen_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="html", server_default="html"
    )
    deploy_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    deployed_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", name="fk_app_user_id_user"),
        nullable=False,
        index=True,
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
    is_delete: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0, server_default="0")
