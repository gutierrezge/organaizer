import cv2
from typing import Optional
from ultralytics import YOLO, SAM
import numpy as np
from scipy.spatial import ConvexHull
from itertools import combinations
from src.model import DetectionConfig
from src.model.detection import Prediction, IdentifiedCornersPoints, sort_values
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)


class BoxDetectionService:


    def __init__(self, config: DetectionConfig = DetectionConfig()):
        self.box_model = YOLO(config.box_model)
        self.sam_model = SAM(config.sam_model)


    def __get_bbox_from_mask__(self, mask: np.ndarray, default_bbox:np.ndarray) -> np.ndarray:
        try:
            y_indices, x_indices = np.where(mask)

            x_min = int(np.min(x_indices))
            x_max = int(np.max(x_indices))
            y_min = int(np.min(y_indices))
            y_max = int(np.max(y_indices))

            return np.array([x_min, y_min, x_max, y_max])
        except:
            return default_bbox


    def __select_best_points__(self, corners:Optional[np.ndarray]) -> Optional[np.ndarray]:
        corners:Optional[np.ndarray] = sort_values(corners)

        if corners is None or len(corners) < 6:
            return None
        
        if len(corners) == 6:
            return corners
        
        def are_points_collinear(points):
            for i in range(2, len(points)):
                area = np.linalg.det(np.array([
                    [points[0][0], points[0][1], 1],
                    [points[1][0], points[1][1], 1],
                    [points[i][0], points[i][1], 1]
                ]))
                if abs(area) > 1e-10:
                    return False
            return True

        def convex_hull_area(points_subset) -> float:
            if len(points_subset) < 3 or points_subset.shape[1] != 2 or are_points_collinear(points_subset):
                return 0
            
            return ConvexHull(points_subset).volume

        max_area:float = 0
        best_points:Optional[np.ndarray] = None

        for subset in combinations(corners, 6):
            subset:np.ndarray = np.array(subset)
            area:float = convex_hull_area(subset)
            if area > max_area:
                max_area:float = area
                best_points:Optional[np.ndarray] = subset

        if best_points is None or len(best_points) != 6:
            return None

        return best_points
    

    def __detect_corners__(self, mask: np.ndarray) -> Optional[IdentifiedCornersPoints]:
        binary_image:np.ndarray = mask.astype(np.uint8) * 255
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if not contours:
            return None
        
        contour:np.ndarray = max(contours, key=cv2.contourArea)
        factor:float = 0.001
        best_result:np.ndarray = None
        for i in range(100):
            factor:float = factor + 0.001
            corners:np.ndarray = np.int32(cv2.approxPolyDP(contour, cv2.arcLength(contour, True)*factor, True))
            
            if best_result is None:
                best_result:np.ndarray = corners
            
            elif len(corners) < len(best_result) and len(corners) >= 6:
                    best_result:np.ndarray = corners
            
            if len(best_result) == 6:
                break
        
        return IdentifiedCornersPoints.build(self.__select_best_points__(best_result))


    def predict(self, frame: np.ndarray) -> Optional[Prediction]:
        box_results = self.box_model.predict(
            source=frame,
            conf=0.5,
            iou=0.5,
            max_det=1,
            verbose=False,
        )[0]

        if (
            box_results is not None
            and box_results.boxes is not None
            and len(box_results.boxes) == 1
        ):
            bbox = np.int32(box_results.boxes[0].xyxy[0].tolist())
            
            sam_result = self.sam_model(
                frame, bboxes=[bbox], verbose=False
            )
            mask:Optional[np.ndarray] = None
            corners:Optional[IdentifiedCornersPoints] = None
            if sam_result is not None and len(sam_result) > 0:
                mask:np.ndarray = sam_result[0].masks.data.cpu().numpy()[0]
                bbox:np.ndarray = self.__get_bbox_from_mask__(mask, bbox)
                corners:Optional[IdentifiedCornersPoints] = self.__detect_corners__(mask)

            return Prediction(bbox=bbox, mask=mask, corners=corners)
        return None