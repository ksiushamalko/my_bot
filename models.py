from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deadlines: Mapped[list["Deadline"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64), default="Общее")
    deadline_at: Mapped[datetime] = mapped_column(DateTime)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_24h: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_1h: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_now: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="deadlines")