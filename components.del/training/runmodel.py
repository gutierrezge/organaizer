import os
import logging
import cv2
from typing import Optional
import numpy as np
from detection.box import BoxDetection, Prediction
import components.training.detection.plot as plot
from detection.volume import DimensionsEstimator
from components.training.detection.models import Prediction


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)
os.makedirs('.data/capture/screenshots', exist_ok=True)


def set_reslution(cap, w: int, h: int, fps: int):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    logging.info(f"Actual: {actual_width}x{actual_height} at {actual_fps}")
    return actual_width, actual_height, actual_fps


def preprocess_frame(frame:np.ndarray) -> np.ndarray:
    denoised:np.ndarray = cv2.bilateralFilter(frame, d=5, sigmaColor=75, sigmaSpace=75)
    gaussian:np.ndarray = cv2.GaussianBlur(denoised, (0, 0), 3.0)
    unsharp_mask:np.ndarray = cv2.addWeighted(denoised, 2.0, gaussian, -1.0, 0)
    
    return np.clip(unsharp_mask, 0, 255)

def main(camera_id=0):
    detection = BoxDetection(".data/runs/train/organaizer4/weights/best.pt", "sam2_t.pt")
    
    
    cap = cv2.VideoCapture(camera_id)

    # Check if camera opened successfully
    if not cap.isOpened():
        logging.info("Error: Could not open camera")
        return
    
    set_reslution(cap, 640, 360, 30)
    estimator = DimensionsEstimator(450, (640, 360), 120)
    logging.info("Press 'q' or 'ESC' to quit")
    try:
        while True:
            found, frame = cap.read()
            original = frame.copy()
            frame = preprocess_frame(frame)
            
            prediction:Optional[Prediction] = detection.predict(frame)
            if prediction is not None:
                prediction.dimensions = estimator.calculate_object_dimensions(prediction)
            
            painted_frame = plot.plot_prediction(original, prediction)
            cv2.imshow("Camera Feed", painted_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
            elif key == ord("x"):
                cv2.waitKey(-1)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
