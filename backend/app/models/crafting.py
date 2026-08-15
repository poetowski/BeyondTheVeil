import enum
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class CraftingCategory(str, enum.Enum):
    ALCHEMY = "alchemy"
    FORGE = "forge"


crafting_category_enum = SAEnum(
    CraftingCategory, name="crafting_category", values_callable=lambda enum_cls: [e.value for e in enum_cls]
)


class CraftingRecipe(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "crafting_recipes"
    __table_args__ = (
        CheckConstraint(
            "(output_consumable_template_id IS NULL) != (output_rune_template_id IS NULL)",
            name="exactly_one_output",
        ),
    )

    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[CraftingCategory] = mapped_column(crafting_category_enum, nullable=False)
    level_requirement: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    output_consumable_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consumable_templates.id"), nullable=True
    )
    output_rune_template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rune_templates.id"), nullable=True
    )
    output_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    ingredients: Mapped[list["CraftingRecipeIngredient"]] = relationship(back_populates="recipe")
    output_consumable_template: Mapped["ConsumableTemplate | None"] = relationship()
    output_rune_template: Mapped["RuneTemplate | None"] = relationship()


class CraftingRecipeIngredient(UUIDPKMixin, Base):
    __tablename__ = "crafting_recipe_ingredients"

    recipe_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("crafting_recipes.id", ondelete="CASCADE"), nullable=False
    )
    material_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_templates.id"), nullable=False
    )
    quantity_required: Mapped[int] = mapped_column(Integer, nullable=False)

    recipe: Mapped["CraftingRecipe"] = relationship(back_populates="ingredients")
    material_template: Mapped["MaterialTemplate"] = relationship()
