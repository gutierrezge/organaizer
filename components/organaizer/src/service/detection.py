import io
import random as rnd
from typing import List, Union
import numpy as np
from threading import Thread
from ultralytics import YOLO
import cv2
from src import log
from src.model import Execution, Box, Clp, DetectedBoxResult, DetetionConfig
from src.dao import ExecutionDAO
from src.service import MinioService

logger = log.configure()
MAX_WIDTH = 300


class YOLOService:

    def __init__(self, config: DetetionConfig = DetetionConfig()):
        self.model = YOLO(config.model)
        self.config = config

    def predict(self, image: Union[str, np.ndarray]) -> List[DetectedBoxResult]:
        results = self.model.predict(
            source=image,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            verbose=False,
        )[0]

        detections: List[DetectedBoxResult] = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]

            detections.append(
                DetectedBoxResult(
                    x1=int(x1),
                    y1=int(y1),
                    x2=int(x2),
                    y2=int(y2),
                    confidence=confidence,
                    class_id=class_id,
                    class_name=class_name,
                )
            )

        return detections

    @classmethod
    def draw_detections(
        cls,
        image: np.ndarray,
        detections: List[Union[DetectedBoxResult, Box]],
        font_weight: float = 1,
        box_border_color: tuple[int, int, int] = (0, 255, 0),
    ) -> np.ndarray:
        img_draw: np.ndarray = image.copy()

        for det in detections:
            cv2.rectangle(
                img_draw,
                (int(det.x1), int(det.y1)),
                (int(det.x2), int(det.y2)),
                color=box_border_color,
                thickness=font_weight,
            )

        return img_draw


class DetectionProcess(Thread):

    def __init__(
        self, execution: Execution, dao: ExecutionDAO, minio_service: MinioService
    ):
        Thread.__init__(self)
        self.execution: Execution = execution
        self.dao: ExecutionDAO = dao
        self.minio_service: MinioService = minio_service
        self.yolo: YOLOService = YOLOService()

    def error(self, message: str):
        logger.error(message, exc_info=True)
        self.dao.update(self.execution.id, "ERROR", message)

    def done(self):
        self.dao.update(self.execution.id, "DONE")
        logger.info(f"Predictions finished for image {self.execution.key}")

    def resize(self, img: np.array, target_width: int = MAX_WIDTH):
        height, width = img.shape[:2]
        new_height: int = int(target_width / (width / height))
        return cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_AREA)

    def run(self):
        try:
            # Get image from storace
            image_bytes: bytes = self.minio_service.get_object_content(
                self.execution.key
            )
            # Convert to numpy image
            image: np.array = cv2.imdecode(
                np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR
            )
            # If image is too big, then resize it
            if image.shape[1] != MAX_WIDTH:
                # Adjust image size and update the storage
                image = self.resize(image)
                _, resized = cv2.imencode(".jpg", image)
                self.minio_service.put_object(
                    self.execution.key, io.BytesIO(resized), resized.size
                )

            # Predict boxes in image
            detections:List[DetectedBoxResult] = self.yolo.predict(image)

            # Predict dimensions
            #############################################################################
            # TODO: REMOVE MOCKED DATA AND COMPUTE VOLUMETRIC DATA FOR EACH PREDICTED BOX
            #############################################################################
            boxes: List[Box] = [
                Box(
                    execution_id=self.execution.id,
                    x1=box.x1,
                    y1=box.y1,
                    x2=box.x2,
                    y2=box.y2,
                    width=rnd.uniform(5, 30),
                    height=rnd.uniform(5, 30),
                    depth=rnd.uniform(5, 30),
                )
                for box in detections
            ]

            # Generate loading plan
            ##################################################################
            # TODO: REMOVE MOCKED DATA AND GENERATE THE CONTAINER LOADING PLAN
            ##################################################################
            plan = [
                Clp(execution_id=self.execution.id, box_id=1, x=0, y=0, z=0),
                Clp(execution_id=self.execution.id, box_id=2, x=1, y=0, z=0),
                Clp(execution_id=self.execution.id, box_id=3, x=2, y=0, z=0),
            ]

            # Save predicted data
            self.dao.delete_boxes(self.execution.id)
            self.dao.save_boxes(boxes)

            self.dao.delete_plan(self.execution.id)
            self.dao.save_plan(plan)

            # Draw predictions and save it
            _, preditect_image = cv2.imencode(
                ".jpg", YOLOService.draw_detections(image, detections)
            )
            self.minio_service.put_object(
                f"{self.execution.id}/result.jpg",
                io.BytesIO(preditect_image),
                preditect_image.size,
            )

            self.done()
        except Exception as e:
            self.error(f"Failed to process image. {self.execution.key}. {str(e)}")
            raise e
