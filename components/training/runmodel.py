import cv2
from ultralytics import YOLO, SAM
import logging
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)


def set_reslution(cap, w: int, h: int, fps: int):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    logging.info(f"Actual: {actual_width}x{actual_height} at {actual_fps}")
    return actual_width, actual_height, actual_fps


def get_bbox_from_mask(mask: np.ndarray):
    y_indices, x_indices = np.where(mask)

    x_min = int(np.min(x_indices))
    x_max = int(np.max(x_indices))
    y_min = int(np.min(y_indices))
    y_max = int(np.max(y_indices))

    return x_min, y_min, x_max, y_max


def predict(box_model: YOLO, sam_model: SAM, frame: np.ndarray) -> dict:
    box_results = box_model.predict(
        source=frame,
        conf=0.5,
        iou=0.5,
        max_det=1,
        verbose=False,
    )[0]

    if (
        box_results is not None
        and box_results.boxes is not None
        and len(box_results.boxes) == 1
    ):
        box = box_results.boxes[0]
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        sam_result = sam_model(
            frame, bboxes=[((int(x1), int(y1)), (int(x2), int(y2)))], verbose=False
        )
        masks = sam_result[0].masks.data.cpu().numpy()

        if len(masks) > 1:
            logging.info(f"masks={len(masks)}")

        mask = masks[0] if masks is not None and len(masks) > 0 else None

        if mask is not None:
            x1, y1, x2, y2 = get_bbox_from_mask(mask)

        return {
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
            "mask": mask,
        }
    return None


def draw_detections(frame: np.ndarray, det: dict) -> np.ndarray:
    if det is not None:
        frame = cv2.rectangle(
            frame,
            (det["x1"], det["y1"]),
            (det["x2"], det["y2"]),
            color=(0, 255, 0),
            thickness=1,
        )
        if det["mask"] is not None:
            mask = np.zeros_like(frame)
            mask[det["mask"] == 1] = (0, 0, 255)
            frame = cv2.addWeighted(frame, 1, mask, 0.5, 0)
    return frame


def main(camera_id=0):
    # Open the camera
    cap = cv2.VideoCapture(camera_id)

    # Check if camera opened successfully
    if not cap.isOpened():
        logging.info("Error: Could not open camera")
        return

    set_reslution(cap, 640, 360, 30)
    logging.info("Press 'q' or 'ESC' to quit")
    try:
        box_model = YOLO(".data/runs/train/organaizer4/weights/best.pt")
        sam_model = SAM("sam2_t.pt")

        while True:
            found, frame = cap.read()

            if found:
                # Get model detections/predictions
                detection = predict(box_model, sam_model, frame)
                # Draw detections if any
                frame = draw_detections(frame, detection)
                cv2.imshow("Camera Feed", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
            # Stop the video
            elif key == ord("s"):
                cv2.waitKey(-1)
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
