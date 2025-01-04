import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask, request
from flask_cors import cross_origin
from uuid import UUID
from typing import Optional, List
from src import log
from src.decorator import rest_api
from src.dao import ExecutionDAO
from src.model.response import HealthStatus
from src.model import Execution, Executions, UploadImagesRequest, UploadImagesResponse, DownloadImagesRequest, PredictedImage
from src.service import MinioService
from src.service.detection import DetectionProcess


load_dotenv(find_dotenv())
logger = log.configure()
app = Flask(__name__)
dao = ExecutionDAO()
minio_service = MinioService()


@app.route("/health-check", methods=["GET"])
@cross_origin()
@rest_api
def health_check() -> HealthStatus:
    return HealthStatus()


@app.route("/executions", methods=["GET"])
@cross_origin()
@rest_api
def executions_list() -> Executions:
    executions:List[Execution] = dao.find_all()
    for execution in executions:
        find_predicted_images(execution)

    return Executions(executions=executions)


def find_predicted_images(execution:Execution) -> Optional[Execution]:
    if execution is not None and execution.status == "DONE":
        images_key:List[str] = minio_service.list_files(f"{execution.id}/prediction/")
        predicted_images:List[PredictedImage] = []
        for key in images_key:
            predicted_images.append(PredictedImage(
                id=UUID(key[key.rfind('/')+1:key.rfind('.')]),
                url=minio_service.generate_presigned_get_url(key),
                boxes=dao.find_boxes(key)
            ))
        execution.predicted_images = predicted_images
    return execution


@app.route("/presigned-put-url", methods=["POST"])
@cross_origin()
@rest_api
def get_presigned_put_urls() -> UploadImagesResponse:
    return minio_service.generate_presigned_put_url(
        UploadImagesRequest(**request.get_json())
    )


@app.route("/execution/<id>", methods=["GET"])
@cross_origin()
@rest_api
def find_execution(id: str) -> Optional[Execution]:
    return find_predicted_images(dao.find_by_id(UUID(id)))


@app.route("/execution", methods=["POST"])
@cross_origin()
@rest_api
def create_execution() -> Execution:
    execution: Execution = dao.save(Execution(**request.get_json()))
    DetectionProcess(execution, dao, minio_service).start()

    return execution

@app.route("/redo/<id>", methods=["POST"])
@cross_origin()
@rest_api
def redo_execution(id: str) -> Execution:
    execution: Execution = dao.find_by_id(UUID(id))
    dao.update(execution.id, 'PROCESSING')
    DetectionProcess(execution, dao, minio_service).start()

    return execution


@app.route("/execution/<id>", methods=["DELETE"])
@cross_origin()
@rest_api
def delete_execution(id: str) -> Optional[Execution]:
    execution: Execution = dao.find_by_id(UUID(id))
    if execution is not None:
        dao.delete(UUID(id))
    return execution


def main():
    debug = (
        True
        if "ORGANAIZER_ADMIN_DEBUG_MODE" not in os.environ
        else os.getenv("ORGANAIZER_ADMIN_DEBUG_MODE") == "True"
    )
    host = (
        "0.0.0.0"
        if "ORGANAIZER_ADMIN_HTTP_HOST" not in os.environ
        else os.getenv("ORGANAIZER_ADMIN_HTTP_HOST")
    )
    port = (
        80
        if "ORGANAIZER_ADMIN_HTTP_PORT" not in os.environ
        else int(os.getenv("ORGANAIZER_ADMIN_HTTP_PORT"))
    )

    log.app_print(
        logger,
        [
            f"Starting HTTP Service!",
            f"{'DEBUG MODE ENABLED' if debug else 'PRODUCTION MODE'}",
            f"HOST: {host}",
            f"PORT: {port}",
        ],
    )

    app.run(debug=debug, host=host, port=port)


if __name__ == "__main__":
    main()
