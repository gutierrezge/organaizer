from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Numeric, String, UUID, Integer, DateTime, ForeignKey, Enum, Text
import enum


Base = declarative_base()


class ExecutionStatus(enum.Enum):
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"


class ExecutionEntity(Base):
    __tablename__ = 'execution'
    id = Column(UUID, primary_key=True)
    key = Column(String, nullable=False)
    container_width = Column(Numeric(precision=15, scale=2), nullable=False)
    container_height = Column(Numeric(precision=15, scale=2), nullable=False)
    container_depth = Column(Numeric(precision=15, scale=2), nullable=False)
    status = Column(Enum(ExecutionStatus), nullable=False)
    status_message = Column(Text, nullable=True)
    created_on = Column(DateTime, nullable=False, default=datetime.now)
    modified_on = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class BoxEntity(Base):
    __tablename__ = 'box'
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(UUID,  ForeignKey('execution.id'), nullable=False)
    x1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    width = Column(Numeric(precision=15, scale=2), nullable=False)
    height = Column(Numeric(precision=15, scale=2), nullable=False)
    depth = Column(Numeric(precision=15, scale=2), nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.now)
    modified_on = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


class ClpEntity(Base):
    __tablename__ = 'clp'
    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(UUID,  ForeignKey('execution.id'), nullable=False)
    box_id = Column(Integer, nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    z = Column(Integer, nullable=False)
    created_on = Column(DateTime, nullable=False, default=datetime.now)
    modified_on = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


def create_entities(engine):
    Base.metadata.create_all(engine)