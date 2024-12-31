import io
import random as rnd
from typing import List, Union
import numpy as np
from threading import Thread
from ultralytics import YOLO
import cv2
from PIL import Image
from src import log
from src.model import (
    Execution,
    DetectedBoxResult,
    DetetionConfig
)
from src.service import MinioService, BoxService, Box, ExecutionService

logger = log.configure()


class DetectionService:


    def __init__(self, config:DetetionConfig=DetetionConfig()):
        self.model = YOLO(config.model)
        self.config = config


    def predict(self, image: Union[str, np.ndarray]) -> List[DetectedBoxResult]:
        results = self.model.predict(
            source=image,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            verbose=False
        )[0]
        
        detections:List[DetectedBoxResult] = []
        for box in results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]
            
            detections.append(DetectedBoxResult(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                confidence=confidence,
                class_id=class_id,
                class_name=class_name
            ))
        
        return detections

    @classmethod
    def draw_detections(cls,
                        image: np.ndarray,
                        detections: List[DetectedBoxResult],
                        font_family:int = cv2.FONT_HERSHEY_SIMPLEX,
                        font_size:float = 0.5,
                        font_weight:float = 1,
                        font_color:tuple[int,int,int] = (0, 0, 0),
                        box_border_color:tuple[int,int,int] = (0, 255, 0)
                        ) -> np.ndarray:
        img_draw:np.ndarray = image.copy()
        
        for det in detections:
            label:str = f"{det.class_name} - {det.confidence*100:.2f}%"
            
            # Draw box
            cv2.rectangle(
                img_draw,
                (int(det.x1), int(det.y1)),
                (int(det.x2), int(det.y2)),
                color=box_border_color,
                thickness=font_weight
            )
            
            # Draw label background
            text_size,_ = cv2.getTextSize(
                label,
                fontFace=font_family,
                fontScale=font_size,
                thickness=font_weight,
            )
            cv2.rectangle(
                img_draw,
                (int(det.x1), int(det.y1 - text_size[1] - 4)),
                (int(det.x1 + text_size[0]), int(det.y1)),
                color=box_border_color,
                thickness=-1
            )

            # Draw label text
            cv2.putText(
                img_draw,
                label,
                (int(det.x1), int(det.y1 - 2)),
                fontFace=font_family,
                fontScale=font_size,
                color=font_color,
                thickness=font_weight
            )
            
        return img_draw
    
class DetectionProcess(Thread):

    def __init__(self,
                 execution:Execution,
                 execution_service:ExecutionService,
                 box_service:BoxService,
                 minio_service:MinioService):
        Thread.__init__(self)
        self.execution:Execution = execution
        self.execution_service:ExecutionService = execution_service
        self.box_service:BoxService = box_service
        self.minio_service = minio_service

    def error(self, message:str):
        logger.error(message, exc_info=True)
        self.execution_service.update(self.execution.id, 'ERROR', message)

    def done(self):
        self.execution_service.update(self.execution.id, 'DONE')
        logger.info(f"Predictions finished for image {self.execution.key}")

    def resize(self, img:np.array, target_width:int = 300):
        height, width = img.shape[:2]
        new_height:int = int(target_width / (width / height))
        return cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_AREA)

    def run(self):
        try:
            image_bytes:bytes = self.minio_service.get_object_content(self.execution.key)
            image:np.array = np.frombuffer(image_bytes, np.uint8)
            image = self.resize(cv2.imdecode(image, cv2.IMREAD_COLOR))
            # Save the image again to ensure we have it in the right size
            _, resized = cv2.imencode('.jpg', image)
            self.minio_service.put_object(self.execution.key, io.BytesIO(resized), resized.size)
        except Exception as e:
            self.error(f"Failed to retrieve image {self.execution.key}")
            raise e

        try:
            detections:List[DetectedBoxResult] = DetectionService().predict(image)
            detections:List[DetectedBoxResult] = [
                DetectedBoxResult(
                    x1=128,
                    y1=113,
                    x2=185,
                    y2=162,
                    confidence=rnd.uniform(0.8, 1),
                    class_id=0,
                    class_name='box'
                ),
                DetectedBoxResult(
                    x1=65,
                    y1=138,
                    x2=176,
                    y2=293,
                    confidence=rnd.uniform(0.8, 1),
                    class_id=0,
                    class_name='box'
                ),
                DetectedBoxResult(
                    x1=183,
                    y1=164,
                    x2=220,
                    y2=271,
                    confidence=rnd.uniform(0.8, 1),
                    class_id=0,
                    class_name='box'
                )
            ]
        except Exception as e:
            self.error(f"Failed to predict the image {self.execution.key}")
            raise e
        
        self.box_service.delete_by_execution_id(self.execution.id)
        for det in detections:
            try:
                # TODO: compute volume
                w,h,d = rnd.uniform(5, 30),rnd.uniform(5, 30),rnd.uniform(5, 30)
            except Exception as e:
                self.error(f"Failed to compute volumen on image {self.execution.key}")
                raise e
            
            try:
                self.box_service.save(Box(
                    execution_id=self.execution.id,
                    x1=det.x1,
                    y1=det.y1,
                    x2=det.x2,
                    y2=det.y2,
                    width=w,
                    height=d,
                    depth=h
                ))
            except Exception as e:
                self.error(f"Failed to save Box data for image {self.execution.key}")
                raise e
        try:
            _, preditect_image = cv2.imencode('.jpg', DetectionService.draw_detections(image, detections))
            self.minio_service.put_object(f"{self.execution.id}/result.jpg", io.BytesIO(preditect_image), preditect_image.size)
        except Exception as e:
            self.error(f"Failed to create predicted image. {self.execution.key}")
            raise e
        # TODO: Generate organization plan and save it to database
        # THIS COULD BE DONE USING GEN-AI using OpenAI, Claude or Gemini??

        self.done()
        