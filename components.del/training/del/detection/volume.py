# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from typing import Optional
from detection.models import Dimensions, IdentifiedCornersPoints
from detection.distance import DistanceEstimator
import numpy as np
import pyrealsense2 as rs
from components.training.del.log import logging

class DimensionsEstimator:


    def __init__(self, distance_estimator:DistanceEstimator):
        self.distance_estimator = distance_estimator


    def calculate_object_dimensions(self, depth_frame:np.ndarray, corners:Optional[IdentifiedCornersPoints]) -> Optional[Dimensions]:
        if corners is None:
            return None
        
        try:
            width = self.__calculate_width__(depth_frame, corners.front, corners.back)
            height = self.__calculate_height__(depth_frame, corners.front, corners.back)
            depth = self.__calculate_depth__(depth_frame, corners.front, corners.back)
            
            return Dimensions(width=width, height=height, depth=depth)
        except:
            logging.error("Failed to do dimensions. ", exc_info=True)
            return None


    def __calculate_width__(
        self,
        depth_frame:rs.depth_frame,
        front_points:np.ndarray,
        back_points:np.ndarray
    ) -> float:
        """
        Calculate object width using the front face points.
        """
        sorted_by_y = front_points[np.argsort(front_points[:, 1])]
        lowest_point = sorted_by_y[-1]
        second_lowest_point = sorted_by_y[-2]

        front_width = self.distance_estimator.distance(depth_frame, lowest_point, second_lowest_point)

        sorted_by_y = front_points[np.argsort(back_points[:, 1])]
        highest_point = sorted_by_y[0]
        second_highest_point = sorted_by_y[1]
        
        back_width = self.distance_estimator.distance(depth_frame, highest_point, second_highest_point)
        
        width = max(front_width, back_width)
        logging.info(f"{highest_point} to {second_lowest_point} = {width:.02f} (width)")
        return float(width)


    def __calculate_height__(
        self,
        depth_frame:rs.depth_frame,
        front_points:np.ndarray,
        back_points:np.ndarray
    ) -> float:
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
        right_height = self.distance_estimator.distance(depth_frame, side1[0], side1[1])
        left_height = self.distance_estimator.distance(depth_frame, side2[0], side2[1])
        
        height = max(right_height, left_height)
        logging.info(f"{side2[0]} to {side2[1]} = {height:.02f} (height)")
        return float(height)


    def __calculate_depth__(
        self,
        depth_frame:rs.depth_frame,
        front_points,
        back_points
    ) -> float:
        """
        Calculate object depth using corresponding front and back points.
        """
        sorted_by_y = front_points[np.argsort(front_points[:, 1])]
        lowest_point_f = sorted_by_y[-1]
        highest_point_f = sorted_by_y[0]
        
        sorted_by_y = front_points[np.argsort(back_points[:, 1])]
        lowest_point_b = sorted_by_y[-1]
        highest_point_b = sorted_by_y[0]
        
        right_depth = self.distance_estimator.distance(depth_frame, lowest_point_f, lowest_point_b)
        left_depth2 = self.distance_estimator.distance(depth_frame, highest_point_f, highest_point_b)
        depth = max(right_depth, left_depth2 )
        logging.info(f"{highest_point_f} to {highest_point_b} = {depth:.02f} (depth)")
        return float(depth)