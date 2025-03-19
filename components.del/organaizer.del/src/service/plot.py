import cv2
from typing import Optional
from src.service.box import Prediction
import numpy as np
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)

class PlotService:
    def plot_prediction(self, frame: np.ndarray, prediction: Optional[Prediction]) -> np.ndarray:
        if prediction is not None:
            thickness:int = 1
            font:int = cv2.FONT_HERSHEY_PLAIN
            scale:float = 0.5
            line_type:int = cv2.LINE_AA
            blue:tuple[int, int, int] = (255, 0, 0)
            green:tuple[int, int, int] = (0, 255, 0)
            red:tuple[int, int, int] = (0, 0, 255)
            white:tuple[int, int, int] = (255, 255, 255)
            circle_size = 3

            if prediction.draw_bbox:
                x1, y1, x2, y2 = prediction.bbox
                frame = cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    color=green,
                    thickness=thickness,
                    lineType=line_type
                )

            
            if prediction.mask is not None:
                if prediction.draw_mask:
                    mask2:np.ndarray = np.zeros_like(frame)
                    mask2[prediction.mask == True] = red
                    frame:np.ndarray = cv2.addWeighted(frame, 1, mask2, 0.5, 0)

                    if mask2.dtype != np.uint8:
                        mask2:np.ndarray = mask2.astype(np.uint8)
                
                    if len(mask2.shape) > 2:
                        mask2:np.ndarray = cv2.cvtColor(mask2, cv2.COLOR_BGR2GRAY)
                    
                    if prediction.draw_edges:
                        contours, _ = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
                        cv2.drawContours(frame, contours, -1, red, thickness, line_type)
                        if prediction.corners is not None:
                            cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.lowest_front_point, red, thickness, line_type)
                            cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.highest_front_point, red, thickness, line_type)
                            cv2.line(frame, prediction.corners.middle_front_point, prediction.corners.middle_highest_back_point, red, thickness, line_type)

                if prediction.corners is not None:
                    if prediction.draw_corners:
                        for i, corner in enumerate(prediction.corners.front):
                            x, y = corner.ravel()
                            cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
                            if prediction.draw_labels:
                                cv2.putText(frame, f'{i} - F - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)
                        for i, corner in enumerate(prediction.corners.back):
                            x, y = corner.ravel()
                            cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
                            if prediction.draw_labels:
                                cv2.putText(frame, f'{i} - B - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)
                        
                        x, y = prediction.corners.middle_front_point.ravel()
                        cv2.circle(frame, (x, y), circle_size, blue, -1, line_type)
                        if prediction.draw_labels:
                            cv2.putText(frame, f'MF - ({x},{y})', (x+5, y), font, scale*2, blue, thickness, line_type)


                if prediction.dimensions is not None:
                    if prediction.draw_dimensions:
                        text = f'w={prediction.dimensions.width:.02f}, h={prediction.dimensions.height:.02f}, d={prediction.dimensions.depth:.02f}'
                        cv2.rectangle(frame, (0,0), (frame.shape[1], 20), white, -1, line_type)
                        cv2.putText(frame, text, (10,15), cv2.FONT_HERSHEY_PLAIN, 1, blue, 1, line_type)
            
        return frame