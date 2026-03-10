import os
import uuid
import json
from sqlalchemy import (
    create_engine,
    Column,
    Text,
    DateTime,
    func,
    ForeignKey,
    UniqueConstraint,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY as PG_ARRAY
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# -----------------------------------------------------------------------------
# Database configuration (handles PostgreSQL URL variations and SQLite fallback)
# -----------------------------------------------------------------------------

def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", os.getenv("POSTGRES_URL", "sqlite:///./app.db"))
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://")
    return url

DATABASE_URL = _get_database_url()

# Add SSL requirement when connecting to a remote Postgres instance
connect_args: dict = {}
if not DATABASE_URL.startswith("sqlite"):
    if "localhost" not in DATABASE_URL and "127.0.0.1" not in DATABASE_URL:
        connect_args["sslmode"] = "require"

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True, echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

# -----------------------------------------------------------------------------
# Table name prefix – prevents collisions when multiple apps share one DB
# -----------------------------------------------------------------------------
PREFIX = "rbl_"

# -----------------------------------------------------------------------------
# SQLAlchemy models
# -----------------------------------------------------------------------------

class Recipe(Base):
    __tablename__ = f"{PREFIX}recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    # Store ingredients as JSON‑encoded list in a Text column (works for SQLite & Postgres)
    ingredients = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tags = relationship("Tag", secondary=f"{PREFIX}recipe_tags", back_populates="recipes")
    ocr_data = relationship("OCRData", back_populates="recipe", cascade="all, delete-orphan")
    ai_recommendations = relationship("AIRecommendation", back_populates="recipe", cascade="all, delete-orphan")

    __table_args__ = (
        Index(f"ix_{PREFIX}recipes_title", "title"),
    )

class Tag(Base):
    __tablename__ = f"{PREFIX}tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)

    recipes = relationship("Recipe", secondary=f"{PREFIX}recipe_tags", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("name", name=f"uq_{PREFIX}tags_name"),
        Index(f"ix_{PREFIX}tags_name", "name"),
    )

class RecipeTag(Base):
    __tablename__ = f"{PREFIX}recipe_tags"

    recipe_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}recipes.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}tags.id", ondelete="CASCADE"), primary_key=True)

class OCRData(Base):
    __tablename__ = f"{PREFIX}ocr_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}recipes.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text, nullable=False)
    processed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recipe = relationship("Recipe", back_populates="ocr_data")

class AIRecommendation(Base):
    __tablename__ = f"{PREFIX}ai_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey(f"{PREFIX}recipes.id", ondelete="CASCADE"), nullable=False)
    suggested_tags = Column(PG_ARRAY(Text))
    confidence_scores = Column(JSON)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recipe = relationship("Recipe", back_populates="ai_recommendations")
