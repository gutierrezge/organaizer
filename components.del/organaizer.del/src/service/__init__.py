import os
import io
from typing import List
from datetime import timedelta
from uuid import uuid4, UUID
from minio import Minio
from src import log
from src.model import (
    UploadImagesResponse,
    UploadImagesRequest,
    UploadImageResponse,
    DownloadImagesRequest,
    DownloadImagesResponse,
)
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())
logger = log.configure()
PUT_EXPIRATION_SECONDS = 5 * 60
GET_EXPIRATION_SECONDS = 60 * 60


class MinioService:

    def __init__(self):
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME")
        self.server = os.getenv("MINIO_SERVER")
        self.client = Minio(
            endpoint=self.server,
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            region=os.getenv("MINIO_REGION"),
            secure=False,
        )
        self._ensure_bucket_exists()


    def _ensure_bucket_exists(self) -> None:
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)


    def generate_presigned_put_url(
        self, request: UploadImagesRequest
    ) -> UploadImagesResponse:
        id = uuid4()
        urls = []
        for file_request in request.files:
            ext = file_request.filename[file_request.filename[:].rfind('.')+1:]
            urls.append(UploadImageResponse(
                id=file_request.id,
                url=self.client.presigned_put_object(
                    bucket_name=self.bucket_name,
                    object_name=f"{str(id)}/source/{file_request.id}.{ext}",
                    expires=timedelta(seconds=PUT_EXPIRATION_SECONDS),
                )
            ))
        
        return UploadImagesResponse(
            id=id,
            urls=urls
        )
    
    def list_files(self, prefix:str) -> List[str]:
        objects:list = self.client.list_objects(
            self.bucket_name,
            prefix=prefix,
        )
        return [obj.object_name for obj in objects]

    def generate_presigned_get_url(self, key:str) -> str:
        return self.client.presigned_get_object(
            bucket_name=self.bucket_name,
            object_name=key,
            expires=timedelta(seconds=GET_EXPIRATION_SECONDS)
        )

    def put_object(self, key: str, data: io.BytesIO, length: int) -> None:
        self.client.put_object(
            bucket_name=self.bucket_name, object_name=key, data=data, length=length
        )

    def get_object_content(self, object_name: str) -> bytes:
        return self.client.get_object(
            bucket_name=self.bucket_name, object_name=object_name
        ).read()

    def delete_object(self, object_name: str) -> None:
        self.client.remove_object(bucket_name=self.bucket_name, object_name=object_name)
