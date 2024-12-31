import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4
from contextlib import contextmanager
import threading
from src.model import Execution, Box
from src.model.entities import ExecutionEntity, BoxEntity, ExecutionStatus, create_entities
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


class DatabaseDetails(BaseModel):
    username:str = Field(default=os.getenv("POSTGRES_USER"))
    password:str = Field(default=os.getenv("POSTGRES_PASSWORD"))
    host:str = Field(default=os.getenv("POSTGRES_HOST"))
    port:str = Field(default=os.getenv("POSTGRES_PORT"))
    dbname:str = Field(default=os.getenv("POSTGRES_DB"))


class Database:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Database, cls).__new__(cls)
                cls._instance._initialize()
            return cls._instance
    
    def _initialize(self):
        details = DatabaseDetails()
        DATABASE_URL = f'postgresql://{details.username}:{details.password}@{details.host}:{details.port}/{details.dbname}'
        self.engine = create_engine(DATABASE_URL)
        self.session_factory = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )

        with self.session() as s:
            create_entities(self.engine)

    @contextmanager
    def session(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

class ExecutionDAO:

    def __init__(self):
        self.db = Database()
    
    def save(self, execution: Execution) -> Execution:
        with self.db.session() as session:
            db_execution = ExecutionEntity(
                id=execution.id,
                key=execution.key,
                container_width=execution.container_width,
                container_height=execution.container_height,
                container_depth=execution.container_depth,
                status=ExecutionStatus[execution.status],
                status_message=None,
                created_on=datetime.now(),
                modified_on=datetime.now()
            )
            execution.created_on = db_execution.created_on
            execution.modified_on = db_execution.modified_on
            session.add(db_execution)
            session.flush()
        return execution

    def find_by_id(self, execution_id: UUID) -> Optional[Execution]:
        with self.db.session() as session:
            e = session.query(ExecutionEntity).filter(ExecutionEntity.id == execution_id).first()
            if e is not None:
                return Execution(
                    id=e.id,
                    key=e.key,
                    container_width=e.container_width,
                    container_height=e.container_height,
                    container_depth=e.container_depth,
                    status=e.status.value,
                    status_message=e.status_message,
                    created_on=e.created_on,
                    modified_on=e.modified_on
                )
        return None
        
    def find_all(self) -> List[Execution]:
        with self.db.session() as session:
            return [
                Execution(
                    id=e.id,
                    key=e.key,
                    container_width=e.container_width,
                    container_height=e.container_height,
                    container_depth=e.container_depth,
                    status=e.status.value,
                    status_message=e.status_message,
                    created_on=e.created_on,
                    modified_on=e.modified_on
                ) for e in session.query(ExecutionEntity).all()
            ]

    def update(self, execution_id: UUID, status:ExecutionStatus, status_message:Optional[str]) -> Optional[Execution]:
        with self.db.session() as session:
            db_execution = session.query(ExecutionEntity).filter(
                ExecutionEntity.id == execution_id
            ).with_for_update().first()
            
            if not db_execution:
                return None
            
            db_execution.status = status
            db_execution.status_message = status_message
        
        return self.find_by_id(execution_id)

    def delete(self, execution_id: UUID) -> bool:
        with self.db.session() as session:
            db_execution = session.query(ExecutionEntity).filter(
                ExecutionEntity.id == execution_id
            ).with_for_update().first()  # Lock the row for deletion
            
            if not db_execution:
                return False
                
            session.delete(db_execution)
        return True


class BoxDAO:


    def __init__(self):
        self.db = Database()
    

    def save(self, box: Box) -> Box:
        with self.db.session() as session:
            session.add(BoxEntity(**box.model_dump(exclude={'volume', 'bbox'})))
            session.flush()
        return box


    def find_by_execution_id(self, execution_id: UUID) -> List[Box]:
        with self.db.session() as session:
            return [
                Box(
                    execution_id=b.execution_id,
                    x1=b.x1,
                    y1=b.y1,
                    x2=b.x2,
                    y2=b.y2,
                    width=b.width,
                    height=b.height,
                    depth=b.depth,
                    created_on=b.created_on,
                    modified_on=b.modified_on
                ) for b in session.query(BoxEntity).filter(BoxEntity.execution_id == execution_id).all()
            ]


    def delete_by_execution_id(self, execution_id: UUID) -> bool:
        with self.db.session() as session:
            boxes = session.query(BoxEntity).filter(
                BoxEntity.execution_id == execution_id
            ).with_for_update().all()
            
            if not boxes or len(boxes) == 0:
                return False
            
            for b in boxes:
                session.delete(b)
        return True