from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class Setting(Base):
    """Singleton-style settings (educator profile + notification toggles).

    We use a flat key/value layout so we can add fields later without migrations.
    Booleans live in `bool_value`, plain strings in `str_value`.
    """

    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    str_value = Column(Text, nullable=True)
    bool_value = Column(Boolean, nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
