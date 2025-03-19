import io
from typing import List, Optional
import numpy as np
from threading import Thread
import cv2
from src import log
from py3dbp import Packer, Bin, Item
from src.service.box import BoxDetectionService
from src.service.plot import PlotService
from src.service.dimensions import DimensionsEstimator
from src.model.detection import Prediction
# from anthropic.types import MessageParam, TextBlockParam, ImageBlockParam
# from anthropic.types.image_block_param import Source

from src.model import (
    Execution,
    Box,
    Clp,
    # DetectedBoxResult,
    # GenAIConfig,
    # EstimatedDimensions,
    # GenerateClpPlanRequest,
    GeneratedClpPlan
)
from src.dao import ExecutionDAO
from src.service import MinioService

logger = log.configure()
MAX_WIDTH = 640


class DetectionProcess(Thread):

    def __init__(
        self, execution: Execution, dao: ExecutionDAO, minio_service: MinioService
    ):
        Thread.__init__(self)
        self.execution: Execution = execution
        self.dao: ExecutionDAO = dao
        self.minio_service: MinioService = minio_service
        self.detection_service: BoxDetectionService = BoxDetectionService()
        self.plot_service: PlotService = PlotService()
        self.dimensions_estimator = DimensionsEstimator(450, (640, 360), 120)


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
    
    def generate_clp(self, boxes:List[Box]) -> Bin:
        packer = Packer()
        container = Bin(
            self.execution.id,
            self.execution.container_width,
            self.execution.container_height,
            self.execution.container_depth,
            1000
        )
        packer.add_bin(container)
        for box in boxes:
            packer.add_item(Item(box.id, box.width, box.height, box.depth, 0))

        packer.pack()
        return container

    def run(self):
        try:
            boxes: List[Box] = []
            logger.info(f"Processing images for execution {self.execution.id}")
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
                prediction:Optional[Prediction] = self.detection_service.predict(image)
                if prediction is not None:
                    prediction.dimensions = self.dimensions_estimator.estimate(prediction)
                    if prediction.dimensions is not None:
                        boxes.append(Box(
                            execution_id=self.execution.id,
                            image_key=prediction_image_key,
                            x1=prediction.bbox[0],
                            y1=prediction.bbox[1],
                            x2=prediction.bbox[2],
                            y2=prediction.bbox[3],
                            width=prediction.dimensions.width,
                            height=prediction.dimensions.height,
                            depth=prediction.dimensions.depth,
                        ))

                image = self.plot_service.plot_prediction(image, prediction)
                # Draw predictions on image and save it
                _, preditect_image = cv2.imencode(".jpg", image)
                self.minio_service.put_object(
                    prediction_image_key,
                    io.BytesIO(preditect_image),
                    preditect_image.size,
                )
            
            self.dao.delete_boxes(self.execution.id)
            self.dao.delete_plan(self.execution.id)
            self.dao.update_plan_remarks(self.execution.id, None)

            # Save predicted boxes
            logger.info(f"Updating boxes for execution {self.execution.id}")
            self.dao.save_boxes(boxes)
            boxes:List[Box] = self.dao.find_boxes_by_execution_id(self.execution.id)
            
            # Generate container loading plan
            if len(boxes) > 0:
                logger.info(f"Generating container loading plan")
                container:Bin = self.generate_clp(boxes)
                remarks = "All boxes fitted in the container."
                if container.unfitted_items is not None and len(container.unfitted_items) > 0:
                    remarks = f"{len(container.unfitted_items)} boxes did not fit in the container."

                plan = GeneratedClpPlan(
                    plan=[
                        Clp(
                            execution_id=self.execution.id,
                            box_id=int(i.name),
                            x=i.position[0],
                            y=i.position[1],
                            z=i.position[2]
                        )
                        for i in container.items
                    ],
                    left_over_boxes=[
                        int(i.name) for i in container.unfitted_items
                    ],
                    remarks=remarks
                )
                logger.info(f"plan={plan}")

                # Save generated plan
                logger.info(f"Updating plan for execution {self.execution.id}")
                if plan is not None:
                    self.dao.save_plan(plan.plan)
                    self.dao.update_plan_remarks(self.execution.id, plan.remarks)
                    self.execution.plan_remarks = plan.remarks

            self.done()
        except Exception as e:
            self.error(f"Failed to process execution {self.execution.id}. {str(e)}")
            raise e
