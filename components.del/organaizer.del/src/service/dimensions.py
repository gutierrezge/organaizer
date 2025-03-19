import numpy as np
from typing import Optional
from src.model.detection import Dimensions, Prediction, IdentifiedCornersPoints
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)

class DimensionsEstimator:


    def __init__(self, focal_length:float, dsize:tuple[int, int], distance_cm:float):
        self.focal_length:float = focal_length
        self.dsize:tuple[int, int] = dsize
        self.distance_cm:float = distance_cm


    def estimate(self, prediction:Prediction) -> Optional[Dimensions]:
        """
        Calculate object dimensions from 6 corner points in image coordinates.
        
        Args:
            points: np.ndarray of shape (6, 2) containing x,y pixel coordinates
                sorted clockwise starting from top-left
            focal_length: focal length in pixels
            image_size: tuple of (width, height) in pixels
            distance_cm: distance from camera to object in centimeters
        
        Returns:
            tuple: (width, height, depth) in centimeters
        """
        if prediction.corners is None:
            return None

        # Convert pixel coordinates to normalized image coordinates
        corners:IdentifiedCornersPoints = prediction.corners
        principal_point:tuple[float, float] = (self.dsize[0] / 2, self.dsize[1] / 2)
        try:
            front_points:np.ndarray = self.__normalize_image_coordinates__(corners.front, principal_point)
            back_points:np.ndarray = self.__normalize_image_coordinates__(corners.back, principal_point)

            # Calculate dimensions
            width = self.__calculate_width__(front_points, back_points)
            height = self.__calculate_height__(front_points, back_points)
            depth = self.__calculate_depth__(front_points, back_points)
            
            return Dimensions(width=width, height=height, depth=depth)
        except:
            return None

    def __normalize_image_coordinates__(self, points:np.ndarray, principal_point:tuple[float, float]) -> np.ndarray:
        """
        Convert pixel coordinates to normalized image coordinates.
        """
        if isinstance(points, list):
            points = np.vstack(points)
        normalized = points.astype(np.float64)
        normalized[:, 0] = (points[:, 0] - principal_point[0]) / self.focal_length
        normalized[:, 1] = (points[:, 1] - principal_point[1]) / self.focal_length
        return normalized


    def __calculate_width__(self, front_points:np.ndarray, back_points:np.ndarray) -> float:
        """
        Calculate object width using the front face points.
        """
        sorted_by_y = front_points[np.argsort(front_points[:, 1])]
        lowest_point = sorted_by_y[-1]
        second_lowest_point = sorted_by_y[-2]

        front_width = np.linalg.norm(lowest_point - second_lowest_point) * self.distance_cm

        sorted_by_y = front_points[np.argsort(back_points[:, 1])]
        highest_point = sorted_by_y[0]
        second_highest_point = sorted_by_y[1]
        
        back_width = np.linalg.norm(highest_point - second_highest_point) * self.distance_cm
        
        return (front_width + back_width) / 2


    def __calculate_height__(self, front_points:np.ndarray, back_points:np.ndarray) -> float:
        """
        Calculate object height using the front face points.
        """
        sorted_by_y = front_points[np.argsort(front_points[:, 1])]
        lowest_point = sorted_by_y[-1]
        sorted_by_y = front_points[np.argsort(back_points[:, 1])]
        highest_point = sorted_by_y[0]
        
        side1 = front_points[
            (front_points != lowest_point).all(axis=1)
        ]
        side2 = back_points[
            (back_points != highest_point).all(axis=1)
        ]

        # Calculate height from front face (first to last point)
        right_height = np.linalg.norm(side1[0] - side1[1]) * self.distance_cm
        left_height = np.linalg.norm(side2[0] - side2[1]) * self.distance_cm
        
        return (right_height + left_height) / 2


    def __calculate_depth__(self, front_points, back_points) -> float:
        """
        Calculate object depth using corresponding front and back points.
        """
        sorted_by_y = front_points[np.argsort(front_points[:, 1])]
        lowest_point_f = sorted_by_y[-1]
        highest_point_f = sorted_by_y[0]
        
        sorted_by_y = front_points[np.argsort(back_points[:, 1])]
        lowest_point_b = sorted_by_y[-1]
        highest_point_b = sorted_by_y[0]
        
        right_depth = np.linalg.norm(lowest_point_f - lowest_point_b) * self.distance_cm
        left_depth2 = np.linalg.norm(highest_point_f - highest_point_b) * self.distance_cm
        return (right_depth + left_depth2 )