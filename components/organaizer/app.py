import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request
from flask_cors import cross_origin
from uuid import UUID
from typing import Optional
from src import log
from src.decorator import rest_api
from src.dao import ExecutionDAO
from src.model.response import HealthStatus
from src.model import Execution, Executions
from src.service import (
    MinioService,
    PresignedUrlRequest,
    PresignedUrlResponse
)
from src.service.detection import DetectionProcess


load_dotenv(find_dotenv())
logger = log.configure()
app = Flask(__name__)
dao = ExecutionDAO()
minio_service = MinioService()


@app.route('/health-check', methods=['GET'])
@cross_origin()
@rest_api
def health_check() -> HealthStatus:
    return HealthStatus()


@app.route('/executions', methods=['GET'])
@cross_origin()
@rest_api
def executions() -> Executions:
    return Executions(executions=dao.find_all())


@app.route('/presigned-put-url', methods=['POST'])
@cross_origin()
@rest_api
def get_presigned_put_urls() -> PresignedUrlResponse:
    return minio_service.generate_presigned_put_url(PresignedUrlRequest(**request.get_json()))


@app.route('/execution/<id>', methods=['GET'])
@cross_origin()
@rest_api
def get_execution(id:str) -> Optional[Execution]:
    execution:Execution = dao.find_by_id(UUID(id))
    if execution is not None and execution.status == 'DONE':
        execution.source_image_url = minio_service.generate_presigned_get_url(PresignedUrlRequest(key=execution.key)).url
        execution.predicted_image_url = minio_service.generate_presigned_get_url(PresignedUrlRequest(key=f"{execution.id}/result.jpg")).url
    return execution


@app.route('/execution', methods=['POST'])
@cross_origin()
@rest_api
def create_execution() -> Execution:
    execution:Execution = dao.save(Execution(**request.get_json()))
    DetectionProcess(execution, dao, minio_service).start()
    
    return execution


@app.route('/execution/<id>', methods=['DELETE'])
@cross_origin()
@rest_api
def delete_execution(id:str) -> Optional[Execution]:
    execution:Execution = dao.find_by_id(UUID(id))
    if execution is not None:
        dao.delete(UUID(id))
    return execution


def main():
    debug = True if 'ORGANAIZER_ADMIN_DEBUG_MODE' not in os.environ else os.getenv('ORGANAIZER_ADMIN_DEBUG_MODE') == 'True'
    host = "0.0.0.0" if 'ORGANAIZER_ADMIN_HTTP_HOST' not in os.environ else os.getenv('ORGANAIZER_ADMIN_HTTP_HOST')
    port = 80 if 'ORGANAIZER_ADMIN_HTTP_PORT' not in os.environ else int(os.getenv('ORGANAIZER_ADMIN_HTTP_PORT'))
    
    log.app_print(logger, [
        f"Starting HTTP Service!",
        f"{'DEBUG MODE ENABLED' if debug else 'PRODUCTION MODE'}",
        f"HOST: {host}",
        f"PORT: {port}"
    ])
    
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()