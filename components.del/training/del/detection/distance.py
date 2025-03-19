# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import numpy as np
import pyrealsense2 as rs
from components.training.del.log import logging

class DistanceEstimator:

    def __init__(self, depth_intrinsics:rs.intrinsics, factor:float):
        self.depth_intrinsics:rs.intrinsics = depth_intrinsics
        self.factor = factor


    def distance(
        self,
        depth_frame:np.ndarray,
        p1: tuple[int, int],
        p2: tuple[int, int]
    ):
        depth1 = depth_frame[p1[1], p1[0]]
        depth2 = depth_frame[p2[1], p2[0]]
            
        point1_3d = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, p1, depth1)
        point2_3d = rs.rs2_deproject_pixel_to_point(self.depth_intrinsics, p2, depth2)
        
        return np.linalg.norm(np.array(point1_3d) - np.array(point2_3d)) * self.factor