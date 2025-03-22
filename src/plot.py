# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


import cv2
from typing import Optional
import numpy as np


THICKNESS:int = 4
FONT:int = cv2.FONT_HERSHEY_PLAIN
FONT_SCALE:float = 2
LINE_TYPE:int = cv2.LINE_AA
COLOR_BLUE:tuple[int, int, int] = (255, 0, 0)
COLOR_GREEN:tuple[int, int, int] = (0, 255, 0)
COLOR_RED:tuple[int, int, int] = (0, 0, 255)
CORNER_SIZE:int = 5

def plot_prediction(
    frame: np.ndarray,
    bbox:Optional[np.ndarray]=None,
    mask:Optional[np.ndarray]=None,
    corners=None,
    draw_bbox:bool=True,
    draw_mask:bool=True,
    draw_corners:bool=True,
    draw_edges:bool=False
) -> np.ndarray:
    """Plots bbox, mask and corners to the given frame"""
    if draw_bbox and bbox is not None:
        x1, y1, x2, y2 = bbox
        frame = cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color=COLOR_GREEN,
            thickness=THICKNESS,
            lineType=LINE_TYPE
        )

    if draw_mask and mask is not None:
        mask2:np.ndarray = np.zeros_like(frame)
        mask2[mask == True] = COLOR_RED
        frame:np.ndarray = cv2.addWeighted(frame, 1, mask2, 0.5, 0)

        if mask2.dtype != np.uint8:
            mask2:np.ndarray = mask2.astype(np.uint8)
    
        if len(mask2.shape) > 2:
            mask2:np.ndarray = cv2.cvtColor(mask2, cv2.COLOR_BGR2GRAY)
        
        if draw_edges:
            contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(frame, contours, -1, COLOR_RED, THICKNESS, LINE_TYPE)
            if corners is not None:
                cv2.line(frame, corners.middle_front_point, corners.lowest_front_point, COLOR_RED, THICKNESS, LINE_TYPE)
                cv2.line(frame, corners.middle_front_point, corners.highest_front_point, COLOR_RED, THICKNESS, LINE_TYPE)
                cv2.line(frame, corners.middle_front_point, corners.middle_highest_back_point, COLOR_RED, THICKNESS, LINE_TYPE)

    if draw_corners and corners is not None:
        for i, corner in enumerate(corners.front):
            x, y = corner.ravel()
            cv2.circle(frame, (x, y), CORNER_SIZE, COLOR_BLUE, -1, LINE_TYPE)
        
        for i, corner in enumerate(corners.back):
            if isinstance(corner, list) or isinstance(corner, np.ndarray):
                x, y = corner.ravel()
                cv2.circle(frame, (x, y), CORNER_SIZE, COLOR_BLUE, -1, LINE_TYPE)

    return frame