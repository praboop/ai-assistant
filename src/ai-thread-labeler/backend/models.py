from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, Double
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector  # Correct import

import uuid

Base = declarative_base()

class Classifications(Base):
    __tablename__ = 'classifications'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)

class Embeddings(Base):
    __tablename__ = 'embeddings'
    message_id = Column(String, ForeignKey('messages.message_id', ondelete="CASCADE"), primary_key=True)
    vector = Column(Vector(768), nullable=False)

class Messages(Base):
    __tablename__ = 'messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    space_id = Column(String, ForeignKey('spaces.room_id', ondelete="CASCADE"), nullable=False)
    message_id = Column(String, unique=True, nullable=False)
    parent_id = Column(String, nullable=True)
    person_id = Column(String, nullable=False)
    person_email = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created = Column(TIMESTAMP, nullable=False)

class ProcessedMessages(Base):
    __tablename__ = 'processed_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete="CASCADE"), nullable=False)
    processed_text = Column(Text, nullable=False)
    solution_detected = Column(String, nullable=False)

class Spaces(Base):
    __tablename__ = 'spaces'
    room_id = Column(String, primary_key=True)
    space_name = Column(String, nullable=False)

class ThreadLabels(Base):
    __tablename__ = 'thread_labels'
    thread_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_label = Column(Text, nullable=False)
    solution_message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id', ondelete="SET NULL"), nullable=True)
    solution_confidence = Column(Double, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
