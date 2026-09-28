import uuid
from datetime import datetime

from sqlalchemy import (
    Column, Text, ForeignKey, ARRAY, TIMESTAMP, Date, CheckConstraint, func, UniqueConstraint, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from pgvector.sqlalchemy import Vector

Base = declarative_base()

EMBEDDING_DIM = 1024  # Cohere embed-multilingual-v3.0


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    issuer = Column(Text, nullable=False)
    date = Column(Text)          # kept as free text: "2025", "Nov 2024", blank, etc.
    field = Column(Text)
    file_url = Column(Text)      # Supabase Storage public URL
    description = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    folder_name = Column(Text, unique=True, nullable=False)  # e.g., "kyc-onboarding"
    github_repo = Column(Text)
    tech_stack = Column(ARRAY(Text))
    start_date = Column(Date)
    end_date = Column(Date)
    summary = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    chunks = relationship("KnowledgeChunk", back_populates="project", cascade="all, delete-orphan")


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        CheckConstraint(
            "source_type in ('personal_bio','experience','project_narrative','github_readme','certification')",
            name="knowledge_chunks_source_type_check",
        ),
        # Unique constraint on file_path + chunk_index for GitHub-ingested chunks
        # Nullable file_path means manually-added chunks won't conflict
        UniqueConstraint("file_path", "chunk_index", name="uq_chunk_source", postgresql_nulls_not_distinct=False),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_type = Column(Text, nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(EMBEDDING_DIM))
    language = Column(Text, default="auto")
    file_path = Column(Text)       # e.g., "projects/kyc-onboarding/architecture.md"
    chunk_index = Column(Integer)  # 0, 1, 2, ... position within file after splitting

    # Phase 5.1: Metadata columns for pre-filtering
    project_name = Column(Text)    # e.g., "kyc" - extracted from file path for projects
    company_name = Column(Text)    # e.g., "elevvo" - extracted from file path for experience

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="chunks")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_active = Column(TIMESTAMP(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("role in ('user','assistant')", name="messages_role_check"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    role = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    tone_tag = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="messages")


class AnswerCache(Base):
    __tablename__ = "answer_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_hash = Column(Text, nullable=False)
    query_embedding = Column(Vector(EMBEDDING_DIM))
    answer = Column(Text, nullable=False)
    sources = Column(ARRAY(Text))
    project_id_tags = Column(ARRAY(Text))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))