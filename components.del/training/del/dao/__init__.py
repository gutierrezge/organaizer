# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from contextlib import contextmanager
import threading
from domain import (
    Execution, Box, Clp
)
from entity import (
    create_entities,
    ExecutionEntity,
    BoxEntity,
    ExecutionStatus,
    ClpEntity,
)
from dotenv import load_dotenv, find_dotenv
from components.training.del.log import logging

load_dotenv(find_dotenv())


class DbConfig(BaseModel):
    username: str = Field(default=os.getenv("POSTGRES_USER"))
    password: str = Field(default=os.getenv("POSTGRES_PASSWORD"))
    host: str = Field(default=os.getenv("POSTGRES_HOST"))
    port: str = Field(default=os.getenv("POSTGRES_PORT"))
    dbname: str = Field(default=os.getenv("POSTGRES_DB"))


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
        details = DbConfig()
        DATABASE_URL = f"postgresql://{details.username}:{details.password}@{details.host}:{details.port}/{details.dbname}"
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
                container_width=execution.container_width,
                container_height=execution.container_height,
                container_depth=execution.container_depth,
                status=ExecutionStatus[execution.status],
                status_message=None,
                created_on=execution.created_on,
                modified_on=execution.modified_on,
            )
            session.add(db_execution)
            session.flush()
        return execution

    def find_by_id(self, execution_id: UUID) -> Optional[Execution]:
        with self.db.session() as session:
            e = (
                session.query(ExecutionEntity)
                .filter(ExecutionEntity.id == execution_id)
                .first()
            )
            if e is not None:
                return self._to_execution_(e, session)
        return None

    def _to_execution_(self, e: ExecutionEntity, session):
        return Execution(
            id=e.id,
            container_width=e.container_width,
            container_height=e.container_height,
            container_depth=e.container_depth,
            status=e.status.value,
            status_message=e.status_message,
            plan_remarks=e.plan_remarks,
            plan=[
                Clp(
                    execution_id=p.execution_id,
                    box_id=p.box_id,
                    x=p.x,
                    y=p.y,
                    z=p.z,
                    created_on=p.created_on,
                    modified_on=p.modified_on,
                )
                for p in session.query(ClpEntity)
                    .filter(ClpEntity.execution_id == e.id)
                    .all()
            ],
            created_on=e.created_on,
            modified_on=e.modified_on,
        )
    
    def find_boxes_by_execution_id(self, execution_id:UUID) -> List[Box]:
        with self.db.session() as session:
            return [
                Box(
                    id=b.id,
                    execution_id=b.execution_id,
                    image_key=b.image_key,
                    x1=b.x1,
                    y1=b.y1,
                    x2=b.x2,
                    y2=b.y2,
                    width=b.width,
                    height=b.height,
                    depth=b.depth,
                    created_on=b.created_on,
                    modified_on=b.modified_on
                )
                for b in session.query(BoxEntity).filter(BoxEntity.execution_id == execution_id).all()
            ]
    
    def find_boxes(self, image_key:str) -> List[Box]:
        with self.db.session() as session:
            return [
                Box(
                    id=b.id,
                    execution_id=b.execution_id,
                    image_key=b.image_key,
                    x1=b.x1,
                    y1=b.y1,
                    x2=b.x2,
                    y2=b.y2,
                    width=b.width,
                    height=b.height,
                    depth=b.depth,
                    created_on=b.created_on,
                    modified_on=b.modified_on
                )
                for b in session.query(BoxEntity).filter(BoxEntity.image_key == image_key).all()
            ]


    def find_all(self) -> List[Execution]:
        with self.db.session() as session:
            return [
                self._to_execution_(e, session)
                for e in session.query(ExecutionEntity).order_by(ExecutionEntity.created_on.desc()).all()
            ]

    def update(
        self,
        execution_id: UUID,
        status: ExecutionStatus,
        status_message: Optional[str] = None,
    ) -> Optional[Execution]:
        with self.db.session() as session:
            db_execution = (
                session.query(ExecutionEntity)
                .filter(ExecutionEntity.id == execution_id)
                .with_for_update()
                .first()
            )

            if not db_execution:
                return None

            db_execution.status = status
            db_execution.status_message = status_message

        return self.find_by_id(execution_id)
    
    def update_plan_remarks(
        self,
        execution_id: UUID,
        plan_remarks: Optional[str] = None,
    ) -> Optional[Execution]:
        with self.db.session() as session:
            db_execution = (
                session.query(ExecutionEntity)
                .filter(ExecutionEntity.id == execution_id)
                .with_for_update()
                .first()
            )

            if not db_execution:
                return None

            db_execution.plan_remarks = plan_remarks

        return self.find_by_id(execution_id)

    def save_boxes(self, boxes: List[Box]) -> List[Box]:
        with self.db.session() as session:
            for box in boxes:
                session.add(BoxEntity(**box.model_dump(exclude={"id", "volume", "bbox", "inplan"})))
            session.flush()
        return boxes

    def save_plan(self, plan: List[Clp]) -> List[Clp]:
        with self.db.session() as session:
            for p in plan:
                session.add(ClpEntity(**p.model_dump()))
            session.flush()
        return plan

    def delete_boxes(self, execution_id: UUID):
        with self.db.session() as session:
            boxes = (
                session.query(BoxEntity)
                .filter(BoxEntity.execution_id == execution_id)
                .with_for_update()
                .all()
            )
            if boxes and len(boxes) > 0:
                for b in boxes:
                    session.delete(b)

    def delete_plan(self, execution_id: UUID):
        with self.db.session() as session:
            plan: List[Clp] = (
                session.query(ClpEntity)
                .filter(ClpEntity.execution_id == execution_id)
                .with_for_update()
                .all()
            )
            if plan and len(plan) > 0:
                for p in plan:
                    session.delete(p)

    def delete(self, execution_id: UUID) -> bool:
        with self.db.session() as session:
            plan: List[Clp] = (
                session.query(ClpEntity)
                .filter(ClpEntity.execution_id == execution_id)
                .with_for_update()
                .all()
            )
            if plan and len(plan) > 0:
                for p in plan:
                    session.delete(p)

            boxes = (
                session.query(BoxEntity)
                .filter(BoxEntity.execution_id == execution_id)
                .with_for_update()
                .all()
            )
            if boxes and len(boxes) > 0:
                for b in boxes:
                    session.delete(b)

            db_execution = (
                session.query(ExecutionEntity)
                .filter(ExecutionEntity.id == execution_id)
                .with_for_update()
                .first()
            )
            if db_execution:
                session.delete(db_execution)
                return True
        return False
