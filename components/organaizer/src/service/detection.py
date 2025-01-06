import io
import os
import time
import base64
import json
from typing import List, Union, Optional
import numpy as np
from threading import Thread
from ultralytics import YOLO, SAM
from anthropic import Anthropic
import cv2
from src import log
from src.model import Execution, Box, Clp, DetectedBoxResult, DetetionConfig, EstimatedDimensions
from src.dao import ExecutionDAO
from src.service import MinioService

logger = log.configure()
MAX_WIDTH = 300
FONT_FACE = cv2.FONT_HERSHEY_PLAIN
MAX_RETRY = 5

class GenAIService:

    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

    def _tobase64_(self, image) -> str:
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')
    
    def analyze_image(self, image) -> Optional[EstimatedDimensions]:
        count = 0
        while count < MAX_RETRY:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [{
                        "type": "text",
                        "text": "Provide the aproximated values for the width, height, depth in centimeters of the box in the image in a JSON format, There is also an aruco of 3.5 by 3.5 centimeters. Do not return anything else but a JSON string. Example json return {\"width\": 20.0, \"height\":5.56, \"depth\":6.7}"
                    }, {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": self._tobase64_(image)
                        }
                    }]
                }]
            )
            try:
                return EstimatedDimensions(**json.loads(response.content[0].text))
            except:
                count += 1
                time.sleep(0.25*2**count)
        logger.error(f"Failed to parse GENAI Response. {response.content[0].text}", exc_info=True)
        return None


class YOLOService:

    def __init__(self, config: DetetionConfig = DetetionConfig()):
        self.box_model = YOLO(config.box_model)
        self.sam_model = SAM(config.sam_model)
        self.config = config

    def get_bbox_from_mask(self, mask):
        # Find the indices where mask is True
        y_indices, x_indices = np.where(mask)
        
        if len(y_indices) == 0 or len(x_indices) == 0:
            return None  # Return None if mask is empty
        
        # Get the bounding box coordinates
        x_min = int(np.min(x_indices))
        x_max = int(np.max(x_indices))
        y_min = int(np.min(y_indices))
        y_max = int(np.max(y_indices))
        
        # Return in format [x_min, y_min, x_max, y_max]
        return [x_min, y_min, x_max, y_max]

    def predict(self, image: Union[str, np.ndarray]) -> Optional[DetectedBoxResult]:
        box_results = self.box_model.predict(
            source=image,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            max_det=1,
            verbose=False,
        )[0]

        for box in box_results.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            sam_result = self.sam_model(image, bboxes=[((int(x1),int(y1)), (int(x2),int(y2)))], verbose=False)
            masks = sam_result[0].masks.data.cpu().numpy()
            mask = masks[0] if masks is not None and len(masks) > 0 else None
            if mask is not None:
                x1,y1, x2, y2 = self.get_bbox_from_mask(mask)
            
            return DetectedBoxResult(
                x1=int(x1),
                y1=int(y1),
                x2=int(x2),
                y2=int(y2),
                mask=mask
            )
        return None

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
                (det.x1, det.y1),
                (det.x2, det.y2),
                color=box_border_color,
                thickness=font_weight,
            )

        return img_draw
    
    @classmethod
    def draw_mask(cls, frame:np.ndarray, mask:np.ndarray, color:tuple[int, int, int]=(0,0,255), alpha:float=0.5):
        colored_mask = np.zeros_like(frame)
        colored_mask[mask == 1] = color
        return cv2.addWeighted(frame, 1, colored_mask, alpha, 0)


class DetectionProcess(Thread):

    def __init__(
        self, execution: Execution, dao: ExecutionDAO, minio_service: MinioService
    ):
        Thread.__init__(self)
        self.execution: Execution = execution
        self.dao: ExecutionDAO = dao
        self.minio_service: MinioService = minio_service
        self.yolo: YOLOService = YOLOService()
        self.genai: GenAIService = GenAIService()

    def error(self, message: str):
        logger.error(message, exc_info=True)
        self.dao.update(self.execution.id, "ERROR", message)

    def done(self):
        self.dao.update(self.execution.id, "DONE")
        logger.info(f"Predictions finished for execution {self.execution.id}")

    def resize(self, img: np.array, target_width: int = MAX_WIDTH):
        height, width = img.shape[:2]
        new_height: int = int(target_width / (width / height))
        return cv2.resize(img, (target_width, new_height), interpolation=cv2.INTER_AREA)

    def run(self):
        try:
            boxes: List[Box] = []
            for key in self.minio_service.list_files(f"{self.execution.id}/source/"):
                prediction_image_key = key.replace("source", "prediction")
                # Get image from storage
                image_bytes: bytes = self.minio_service.get_object_content(key)
                
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
                        key, io.BytesIO(resized), resized.size
                    )

                # Predict boxes in image
                detection:Optional[DetectedBoxResult] = self.yolo.predict(image)

                if detection is not None:
                    dimensions = self.genai.analyze_image(image)
                    image = YOLOService.draw_detections(image, [detection])
                    if dimensions is not None:
                        box = Box(
                            execution_id=self.execution.id,
                            image_key=prediction_image_key,
                            x1=detection.x1,
                            y1=detection.y1,
                            x2=detection.x2,
                            y2=detection.y2,
                            width=dimensions.width,
                            height=dimensions.height,
                            depth=dimensions.depth,
                        )
                        if detection.mask is not None:
                            image = YOLOService.draw_mask(image, detection.mask)

                        # Draw predictions on image and save it
                        _, preditect_image = cv2.imencode(".jpg", image)
                        self.minio_service.put_object(
                            prediction_image_key,
                            io.BytesIO(preditect_image),
                            preditect_image.size,
                        )
                        boxes.append(box)
            
            # Generate container loading plan
            ##################################################################
            # TODO: REMOVE MOCKED DATA AND GENERATE THE CONTAINER LOADING PLAN
            ##################################################################
            plan = [
                Clp(execution_id=self.execution.id, box_id=1, x=0, y=0, z=0),
                Clp(execution_id=self.execution.id, box_id=2, x=1, y=0, z=0),
                Clp(execution_id=self.execution.id, box_id=3, x=2, y=0, z=0),
            ]

            # Save predicted boxes
            self.dao.delete_boxes(self.execution.id)
            self.dao.save_boxes(boxes)

            # Save generated plan
            self.dao.delete_plan(self.execution.id)
            self.dao.save_plan(plan)

            self.done()
        except Exception as e:
            self.error(f"Failed to process execution {self.execution.id}. {str(e)}")
            raise e
