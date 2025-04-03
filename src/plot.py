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
COLOR_BLACK:tuple[int, int, int] = (0, 0, 0)
COLOR_MAGENTA:tuple[int, int, int] = (255, 0, 255)
COLOR_CYAN:tuple[int, int, int] = (255, 255, 0)
COLOR_YELLOW:tuple[int, int, int] = (0, 255, 255)
COLOR_WHITE:tuple[int, int, int] = (255, 255, 255)
COLOR_GREEN:tuple[int, int, int] = (0, 255, 0)
COLOR_RED:tuple[int, int, int] = (0, 0, 255)
CORNER_SIZE:int = 2

def plot_prediction(
    frame: np.ndarray,
    bbox:Optional[np.ndarray]=None,
    mask:Optional[np.ndarray]=None,
    dimensions=None,
    draw_bbox:bool=True,
    draw_mask:bool=True,
    draw_corner_values:bool=False,
    draw_corners:bool=True,
    draw_distance:bool=True
) -> np.ndarray:
    """Plots bbox, mask and corners to the given frame"""
    if draw_bbox and bbox is not None:
        x1, y1, x2, y2 = bbox
        frame = cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            color=COLOR_GREEN,
            thickness=1,
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
    
    if draw_corners and dimensions is not None:
        draw_side(frame, dimensions.side4, COLOR_CYAN, draw_distance, draw_corner_values)
        draw_side(frame, dimensions.side5, COLOR_MAGENTA, draw_distance, draw_corner_values)
        draw_side(frame, dimensions.side3, COLOR_BLUE, draw_distance, draw_corner_values)


    return frame

def draw_side(frame, side, color1, draw_distance:bool=True, draw_corner_values:bool=True):
    x, y = side.point1
    cv2.circle(frame, (x, y), CORNER_SIZE, color1, -1, LINE_TYPE)
    if draw_corner_values:
        cv2.rectangle(frame, (x+10, y-40), (x+150,y-5), COLOR_WHITE, -1)
        cv2.rectangle(frame, (x+10, y-40), (x+150, y-5), color1, THICKNESS)
        cv2.putText(frame, f"{x},{y}", (x+15,y-10), FONT, FONT_SCALE, COLOR_BLACK, 1, LINE_TYPE)

    x, y = side.point2
    cv2.circle(frame, (x,y), CORNER_SIZE, color1, -1, LINE_TYPE)
    if draw_corner_values:
        cv2.rectangle(frame, (x+10, y-40), (x+150,y-5), COLOR_WHITE, -1)
        cv2.rectangle(frame, (x+10, y-40), (x+150, y-5), color1, THICKNESS)
        cv2.putText(frame, f"{x},{y}", (x+15,y-10), FONT, FONT_SCALE, COLOR_BLACK, 1, LINE_TYPE)

    if draw_distance:
        x1, y1 = side.point1
        x2, y2 = side.point2
        x = int(abs((x2+x1) //2))
        y = int(abs((y2+y1) //2))

        cv2.rectangle(frame, (x-10, y-20), (x+70, y+5), COLOR_WHITE, -1)
        cv2.rectangle(frame, (x-10, y-20), (x+70, y+5), color1, 1)
        cv2.putText(frame, f"{side.value}cm", (x,y), FONT, 1, COLOR_BLACK, 1, LINE_TYPE)

