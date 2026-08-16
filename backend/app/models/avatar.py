from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class AvatarTemplate(UUIDPKMixin, TimestampMixin, Base):
    """A selectable hero portrait. Cosmetic only - no price/level_requirement,
    every avatar is available to every hero from the start."""

    __tablename__ = "avatar_templates"

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
