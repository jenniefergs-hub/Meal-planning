from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    LargeBinary,
)
from sqlalchemy.orm import relationship

from .database import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    quantity = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    category = Column(String, nullable=True)
    source = Column(String, default="manual")  # manual | gmail
    raw_text = Column(Text, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=True)


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    source_type = Column(String, default="book")  # book | manual_online
    book_name = Column(String, nullable=True)
    url = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    servings = Column(Integer, default=1)
    calories_per_serving = Column(Float, nullable=False)
    prep_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    times_cooked = Column(Integer, default=0)
    last_cooked_at = Column(DateTime, nullable=True)
    image_data = Column(LargeBinary, nullable=True)
    image_content_type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated

    ingredients = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )
    ratings = relationship(
        "RecipeRating", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    name = Column(String, nullable=False)
    quantity = Column(String, nullable=True)
    unit = Column(String, nullable=True)

    recipe = relationship("Recipe", back_populates="ingredients")


class RecipeRating(Base):
    __tablename__ = "recipe_ratings"
    __table_args__ = (UniqueConstraint("recipe_id", "member_name", name="uq_recipe_member"),)

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    member_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    rated_at = Column(DateTime, default=datetime.utcnow)

    recipe = relationship("Recipe", back_populates="ratings")


class GmailProcessedMessage(Base):
    __tablename__ = "gmail_processed_messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String, unique=True, nullable=False)
    processed_at = Column(DateTime, default=datetime.utcnow)
    item_count = Column(Integer, default=0)


class PendingReceiptItem(Base):
    __tablename__ = "pending_receipt_items"

    id = Column(Integer, primary_key=True)
    message_id = Column(String, nullable=False)
    email_subject = Column(String, nullable=True)
    raw_line = Column(Text, nullable=True)
    parsed_name = Column(String, nullable=False)
    parsed_quantity = Column(String, nullable=True)
    parsed_unit = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | approved | rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
