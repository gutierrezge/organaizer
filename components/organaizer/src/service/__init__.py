import os
import io
from datetime import timedelta
from uuid import uuid4
from minio import Minio
from src import log
from src.model import (
    PresignedUrlRequest,
    PresignedUrlResponse
)
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
    
    def put_object(self, key:str, data:io.BytesIO, length:int) -> None:
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