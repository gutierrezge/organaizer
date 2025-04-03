# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import numpy as np
from config import Config
import pyrealsense2 as rs

class DistanceEstimator:

    def __init__(self, depth_intrinsics:rs.intrinsics, config:Config):
        self.depth_intrinsics:rs.intrinsics = depth_intrinsics
        self.config = config

    def get_stable_value(self, depth_frame:np.ndarray, p1: tuple[int, int], sigma:float=1.5, k=11):
        y, x = p1
        h, w = depth_frame.shape

        # Define region bounds (clamp to image boundaries)
        x_min = max(x - k, 0)
        x_max = min(x + k + 1, w)
        y_min = max(y - k, 0)
        y_max = min(y + k + 1, h)

        # Extract region and flatten
        region = depth_frame[y_min:y_max, x_min:x_max].flatten()

        # Remove NaNs or zeros if needed
        region = region[~np.isnan(region)]
        region = region[region > 0]

        if len(region) == 0:
            return 0  # Or np.nan, or raise an error

        # IQR filtering
        q1 = np.percentile(region, 25)
        q3 = np.percentile(region, 75)
        iqr = q3 - q1

        lower_bound = q1 - sigma * iqr
        upper_bound = q3 + sigma * iqr

        filtered_data = region[(region >= lower_bound) & (region <= upper_bound)]

        if len(filtered_data) == 0:
            return int(np.median(region))  # fallback to unfiltered median

        return int(np.median(filtered_data))


    def distance(
        self,
        depth_frame:np.ndarray,
        p1: tuple[int, int],
        p2: tuple[int, int]
    ):
        depth1 = self.get_stable_value(depth_frame, p1)
        depth2 = self.get_stable_value(depth_frame, p2)

        point1_3d = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, p1, depth1)
        point2_3d = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, p2, depth2)
        
        return np.linalg.norm(np.array(point1_3d) - np.array(point2_3d)) * self.config.distance.to_centimeter * self.config.distance.distance_factor