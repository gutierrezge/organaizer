import cv2
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s")


def set_reslution(cap, w, h, fps):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    logging.info(f"Actual: {actual_width}x{actual_height} at {actual_fps}")
    return actual_width, actual_height, actual_fps


def open_camera(camera_id=0):
    # Open the camera
    cap = cv2.VideoCapture(camera_id)
    try:
        w, h, fps = set_reslution(cap, 640, 360, 30)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            logging.info("Error: Could not open camera")
            return

        logging.info("Press 'q' or 'ESC' to quit")
        out = None
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        CHECKERBOARD=(8, 6)
        os.makedirs('.data/capture/screenshots', exist_ok=True)
        os.makedirs('.data/capture/video', exist_ok=True)

        while True:
            found, original = cap.read()
            if found:
                frame = original.copy()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                flags = cv2.CALIB_CB_ADAPTIVE_THRESH +  cv2.CALIB_CB_NORMALIZE_IMAGE + cv2.CALIB_CB_FAST_CHECK
                checkboard_image, corners = cv2.findChessboardCorners(gray, CHECKERBOARD, flags)
                if checkboard_image:
                    frame = cv2.drawChessboardCorners(frame, CHECKERBOARD, corners, found)

                cv2.imshow('Camera Feed', frame)
                if out is not None:
                    out.write(original)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') and checkboard_image:
                filename:str = f'.data/capture/screenshots/screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                cv2.imwrite(filename, original)
            elif key == ord('v'):
                if out is None:
                    out = cv2.VideoWriter(f'.data/capture/video/{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4', fourcc, fps, (w, h))
                    logging.info("Recording started.")
                else:
                    out.release()
                    out = None
                    logging.info("Recording stopped.")
            elif key == ord('q') or key == 27:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    open_camera()