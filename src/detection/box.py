# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import cv2
from uuid import uuid4
from typing import Optional, List
from ultralytics import YOLO, SAM
import numpy as np
from scipy.spatial import ConvexHull
from itertools import combinations
from config import Config
from detection.volume import DimensionsEstimator, DistanceEstimator
from domain import Prediction, Dimensions, DimSide
import pyrealsense2 as rs
import utils
import plot

OBJECT_LOST_SECONDS = 5*1000 # 5 seconds

class Tracker:

    def __init__(self):
        self.tracked_dimensions:List[Dimensions] = []
        self.maxlen = 100

    def get_stable_value(self, data:List[float], sigma:float=3):
        data_array = np.array(data)

        # Calculate Q1 and Q3
        q1 = np.percentile(data_array, 25)
        q3 = np.percentile(data_array, 75)
        iqr = q3 - q1

        # Define bounds
        lower_bound = q1 - sigma * iqr
        upper_bound = q3 + sigma * iqr

        # Filter out outliers
        filtered_data = data_array[(data_array >= lower_bound) & (data_array <= upper_bound)]
        return int(np.median(filtered_data))


    def get_sides(self):
        dimension = self.tracked_dimensions[-1]
        if len(self.tracked_dimensions) < 10:
            return dimension.side3, dimension.side4, dimension.side5
        
        side3, side4, side5 = [], [], []
        for pred in self.tracked_dimensions:
            side3.append(dimension.side3.value)
            side4.append(dimension.side4.value)
            side5.append(dimension.side5.value)

        side3 = self.get_stable_value(side3)
        side4 = self.get_stable_value(side4)
        side5 = self.get_stable_value(side5)

        side3 = DimSide(
            value=side3,
            point1=dimension.side3.point1,
            point2=dimension.side3.point2
        )
        side4 = DimSide(
            value=side4,
            point1=dimension.side4.point1,
            point2=dimension.side4.point2
        )
        side5 = DimSide(
            value=side5,
            point1=dimension.side5.point1,
            point2=dimension.side5.point2
        )
        return side3, side4, side5

    def update(self, dimension: Optional[Dimensions]):
        if dimension:
            if len(self.tracked_dimensions) > 0 and (dimension.detection_time - self.tracked_dimensions[-1].detection_time) > OBJECT_LOST_SECONDS:
                self.tracked_dimensions = []

            if dimension:
                self.tracked_dimensions.append(dimension)
                self.tracked_dimensions = self.tracked_dimensions[-self.maxlen:]
                if len(self.tracked_dimensions) > 5:
                    side3, side4, side5 = self.get_sides()
                    return dimension.model_copy(update={
                        "sides": [
                            dimension.side1,
                            dimension.side2,
                            side3,
                            side4,
                            side5,
                            dimension.side6
                        ]
                    })
                else:
                    return dimension

        return dimension

class BoxDetection:


    def __init__(self, config:Config):
        self.config = config
        self.box_model_file = config.detection.box_model
        self.sam_model_file = config.detection.sam_model
        self.tracker = Tracker()
        

    
    def init(self, depth_intrinsics:rs.intrinsics):
        self.box_model = YOLO(self.box_model_file)
        self.sam_model = SAM(self.sam_model_file)
        self.estimator = DimensionsEstimator(DistanceEstimator(depth_intrinsics, self.config))

    
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


    def __select_best_points__(self, corners: Optional[np.ndarray]) -> Optional[np.ndarray]:
        corners = utils.sort_values(corners)
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

        max_area = 0
        best_points = None

        for subset in combinations(corners, 6):
            subset = np.array(subset)
            area = convex_hull_area(subset)
            if area > max_area:
                max_area = area
                best_points = subset

        return best_points if best_points is not None and len(best_points) == 6 else None
    

    def __detect_corners__(self, mask: np.ndarray) -> Optional[np.ndarray]:
        binary_image = (mask.astype(np.uint8)) * 255
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return None

        contour = max(contours, key=cv2.contourArea)
        best_result = None
        factor = 0.001

        for _ in range(100):
            factor += 0.001
            epsilon = cv2.arcLength(contour, True) * factor
            corners = cv2.approxPolyDP(contour, epsilon, True)

            corners = corners.reshape(-1, 2)
            if best_result is None:
                best_result = corners
            elif len(corners) < len(best_result) and len(corners) >= 6:
                best_result = corners

            if len(best_result) == 6:
                break

        return self.__select_best_points__(best_result)
    
    def optimize_mask(self, mask: np.ndarray, depth_frame:np.ndarray) -> np.ndarray:
        object_depth_values = depth_frame[mask]

        q1, q3 = np.percentile(object_depth_values, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - self.config.detection.mask_optimization_sigma * iqr
        upper_bound = q3 + self.config.detection.mask_optimization_sigma * iqr

        return (mask & (depth_frame >= lower_bound) & (depth_frame <= upper_bound))


    def predict(self, frame: np.ndarray, enhanced: np.ndarray, depth_frame:np.ndarray) -> Prediction:
        box_results = self.box_model.predict(
            source=enhanced,
            conf=self.config.detection.confidence,
            iou=self.config.detection.iou,
            max_det=100,
            verbose=False,
        )
        
        for box_result in box_results:
        
            if box_result and box_result.boxes and len(box_result.boxes) > 0:
                for box in box_result.boxes:
                    bbox = np.int32(box.xyxy[0].tolist())
                    bbox_area = (bbox[2]-bbox[0])*(bbox[3]-bbox[1])
                    frame_area = enhanced.shape[0]*enhanced.shape[1]
                    bbox_pct = bbox_area/ frame_area
                    
                    # Ensure we are not getting a weird detection taking almos the whole screen
                    if bbox_pct > 0.05 and bbox_pct < 0.6:
                        sam_result = self.sam_model(
                            enhanced, bboxes=[bbox], verbose=False
                        )
                        
                        if sam_result is not None and len(sam_result) > 0:
                            mask:np.ndarray = sam_result[0].masks.data.cpu().numpy()[0]
                            bbox:np.ndarray = self.__get_bbox_from_mask__(mask, bbox)
                            corners:Optional[np.ndarray] = self.__detect_corners__(mask)
                            if corners is not None:
                                dimensions:Optional[Dimensions] = self.estimator.calculate_object_dimensions(depth_frame, corners)
                                dimensions:Optional[Dimensions] = self.tracker.update(dimensions)
                                return Prediction(
                                    id=uuid4(),
                                    frame=frame,
                                    painted_frame=plot.plot_prediction(frame.copy(), bbox, mask, dimensions),
                                    bbox=bbox,
                                    mask=mask,
                                    corners=corners,
                                    dimensions=dimensions
                                )
                            else:
                                continue
                        else:
                            continue
                    else:
                        continue
        self.tracker.update(None)
        return Prediction(
            id=uuid4(),
            frame=frame,
            painted_frame=plot.plot_prediction(frame.copy())
        )
            
            