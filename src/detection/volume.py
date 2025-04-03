# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from typing import List
from domain import Dimensions, DimSide
from detection.distance import DistanceEstimator
import numpy as np


class DimensionsEstimator:


    def __init__(self, distance_estimator:DistanceEstimator):
        self.distance_estimator = distance_estimator


    def calculate_object_dimensions(self, depth_frame:np.ndarray, corners:np.ndarray) -> Dimensions:
        
        sides:List[DimSide] = []
        for i, corner in enumerate(corners):
            next_corner = corners[0] if len(corners)-1 == i else corners[i+1]
            distance = self.distance_estimator.distance(depth_frame, corner, next_corner)
            sides.append(DimSide(
                value=int(distance),
                point1=corner,
                point2=next_corner
            ))
        return Dimensions(sides=sides)
