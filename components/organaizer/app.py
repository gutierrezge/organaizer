import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request
from flask_cors import CORS
from uuid import UUID
from typing import Optional
from src import log
from src.decorator import rest_api
from src.model.response import HealthStatus
from src.model import Execution, Executions
from src.service import ExecutionService, BoxService, MinioService, PresignedUrlRequest, PresignedUrlResponse


load_dotenv(find_dotenv())
logger = log.configure()
app = Flask(__name__)
execution_service = ExecutionService()
box_service = BoxService()


CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:4200"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "expose_headers": ["Content-Range", "X-Content-Range"],
        "max_age": 3600
    }
})

@app.route('/health-check', methods=['GET'])
@rest_api
def health_check() -> HealthStatus:
    return HealthStatus()


@app.route('/executions', methods=['GET'])
@rest_api
def executions() -> Executions:
    return execution_service.find_all()


@app.route('/presigned-put-url', methods=['POST'])
@rest_api
def get_presigned_put_urls() -> PresignedUrlResponse:
    return MinioService().generate_presigned_put_url(PresignedUrlRequest(**request.get_json()))


@app.route('/execution/<id>', methods=['GET'])
@rest_api
def get_execution(id:str) -> Optional[Execution]:
    return execution_service.find_by_id(UUID(id))


@app.route('/execution', methods=['POST'])
@rest_api
def create_execution() -> Execution:
    logger.info(request.get_json())
    execution:Execution = execution_service.save(Execution(**request.get_json()))
    #TODO: RUN AI HERE
    
    return execution


@app.route('/execution/<id>', methods=['DELETE'])
@rest_api
def delete_execution(id:str) -> Optional[Execution]:
    execution:Execution = execution_service.find_by_id(UUID(id))
    if execution is not None:
        box_service.delete_execution_id(UUID(id))
        execution_service.delete(UUID(id))
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