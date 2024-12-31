import os
import io
from datetime import timedelta
from uuid import uuid4, UUID
from typing import Optional
from minio import Minio
from src import log
from src.model import (
    PresignedUrlRequest,
    PresignedUrlResponse,
    Box,
    Execution,
    Executions,
    ExecutionStatus
)
from src.dao import ExecutionDAO, BoxDAO
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


logger = log.configure()


class MinioService:

    def __init__(self):
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME")
        self.server = os.getenv("MINIO_SERVER")
        self.client = Minio(
            endpoint=self.server,
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            region=os.getenv('MINIO_REGION'),
            secure=False
        )
        
        # Ensure bucket exists
        self._ensure_bucket_exists()


    def _ensure_bucket_exists(self) -> None:
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)


    def generate_presigned_put_url(self, request: PresignedUrlRequest) -> PresignedUrlResponse:
        id = uuid4()
        key = f'{id}/{request.key}'
        url = self.client.presigned_put_object(
            bucket_name=self.bucket_name,
            object_name=key,
            expires=timedelta(seconds=request.expiration)
        )

        return PresignedUrlResponse(
            id=id,
            key=key,
            url=url,
            expiration=request.expiration
        )


    def generate_presigned_get_url(self, request: PresignedUrlRequest) -> PresignedUrlResponse:
        url = self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=request.key,
            expires=timedelta(seconds=request.expiration)
        )

        return PresignedUrlResponse(
            id=request.key[:request.key.find('/')],
            key=request.key,
            url=url,
            expiration=request.expiration
        )
    
    def put_object(self, key:str, data:io.BytesIO, length:int):
        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=key,
            data=data,
            length=length
        )


    def get_object_content(self, object_name: str) -> bytes:
        return self.client.get_object(
            bucket_name=self.bucket_name,
            object_name=object_name
        ).read()


    def delete_object(self, object_name: str) -> None:
        self.client.remove_object(
            bucket_name=self.bucket_name,
            object_name=object_name
        )


class ExecutionService:


    def __init__(self):
        self.execution_dao = ExecutionDAO()
        self.box_dao = BoxDAO()


    def save(self, execution: Execution) -> Execution:
        execution: Execution = self.execution_dao.save(execution)
        return execution
    

    def find_all(self) -> Executions:
        executions = []
        
        for e in self.execution_dao.find_all():
            e.boxes = self.box_dao.find_by_execution_id(e.id)
            executions.append(e)
        
        return Executions(executions=executions)


    def find_by_id(self, id: UUID) -> Optional[Execution]:
        execcution:Optional[Execution] = self.execution_dao.find_by_id(id)
        if not execcution:
            return None
            
        execcution.boxes = self.box_dao.find_by_execution_id(id)
        return execcution


    def update(self, id: UUID, status:ExecutionStatus, status_message:Optional[str]=None) -> Optional[Execution]:
        return self.execution_dao.update(id, status, status_message)


    def delete(self, id: UUID) -> bool:
        return self.execution_dao.delete(id)


class BoxService:


    def __init__(self):
        self.box_dao = BoxDAO()


    def save(self, box: Box) -> Box:
        return self.box_dao.save(box)


    def find_by_execution_id(self, execution_id: UUID) -> list[Box]:
        return self.box_dao.find_by_execution_id(execution_id)


    def delete_by_execution_id(self, execution_id: UUID) -> bool:
        return self.box_dao.delete_by_execution_id(execution_id)