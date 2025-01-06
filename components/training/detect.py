import cv2
import numpy as np
from ultralytics import YOLO, SAM
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s")
COLORS = [
    (0, 0, 255),      # Red
    (0, 255, 0),      # Green
    (255, 0, 0),      # Blue
    (0, 255, 255),    # Yellow
    (255, 0, 255),    # Purple
    (255, 255, 0),    # Cyan
    (0, 165, 255),    # Orange
    (147, 20, 255),   # Pink
    (128, 128, 0),    # Teal
    (0, 255, 191),    # Lime
    (42, 42, 165),    # Brown
    (128, 0, 0),      # Navy
    (80, 127, 255),   # Coral
    (0, 0, 128),      # Maroon
    (160, 255, 160),  # Mint
    (0, 128, 128),    # Olive
    (255, 182, 193),  # Lavender
    (235, 206, 135),  # Sky Blue
    (0, 215, 255),    # Gold
    (0, 128, 0)       # Forest Green
]

def load_models():
    boxes_model = YOLO('runs/train/yolov11_box14/weights/best.pt')
    sam_model = SAM("sam2_t.pt")
    return boxes_model, sam_model

def load_calibration():
    """
    Load camera calibration data from saved numpy files
    """
    camera_matrix = np.load('calibration/camera_matrix.npy')
    dist_coeffs = np.load('calibration/dist_coeffs.npy')
    logging.info(camera_matrix)
    logging.info(dist_coeffs)
    return camera_matrix, dist_coeffs

load_calibration()

def set_reslution(cap, w, h, fps):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cap.set(cv2.CAP_PROP_FPS, fps)

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
    print(f"Actual: {actual_width}x{actual_height} at {actual_fps}")
    return actual_width, actual_height, actual_fps

def estimate_box_volume(frame, masks, camera_matrix, dist_coeffs, aruco_size_cm = 3.5  ):
    # 1. Detect ArUco marker for scale reference
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray)
    
    if ids is not None:
        mask = masks[0]
        
        # 4. Get contours from mask
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        box_contour = max(contours, key=cv2.contourArea)
        cv2.drawContours(frame, contours, -1, (255,0,0), 1)
        
        # 5. Find minimal rectangle that fits the box
        rect = cv2.minAreaRect(box_contour)
        box_points = cv2.boxPoints(rect)
        box_points = np.int8(box_points)
        
        # 6. Calculate pixel to cm ratio using ArUco marker
        aruco_pixel_length = np.linalg.norm(corners[0][0][0] - corners[0][0][1])
        pixels_per_cm = aruco_pixel_length / aruco_size_cm
        
        # 7. Get box dimensions in pixels
        width = np.linalg.norm(box_points[0] - box_points[1])
        height = np.linalg.norm(box_points[1] - box_points[2])
        
        # Convert to real-world dimensions (cm)
        real_width = width / pixels_per_cm
        real_height = height / pixels_per_cm
        
        # 8. Estimate depth using perspective information
        # This is a simplified approach - you might want to use more sophisticated methods
        # Using camera calibration to improve depth estimation
        object_points = np.float32([[0,0,0], [real_width,0,0], [real_width,real_height,0], [0,real_height,0]])
        image_points = box_points.astype(np.float32)
        
        # Solve PnP to get rotation and translation vectors
        success, rvec, tvec = cv2.solvePnP(object_points, image_points, camera_matrix, dist_coeffs)
        
        # Estimate depth from translation vector
        depth = np.linalg.norm(tvec[2])
        
        # 9. Calculate volume
        volume = real_width * real_height * depth
        cv2.rectangle(frame, (0,0), (frame.shape[1], 50), (255,255,255), -1)
        cv2.putText(frame, f"{real_width:.02f},{real_height:.02f}, {depth:.02f} = {volume:.02f}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 1)

        return volume, real_width, real_height, depth, frame
    return None, None, None, None, frame


def estimate_depth(mask, aruco_corners, scale):
    # Get the bounding box of the mask
    x_coords = np.where(np.any(mask, axis=0))[0]
    y_coords = np.where(np.any(mask, axis=1))[0]

    if len(x_coords) == 0 or len(y_coords) == 0:
        raise ValueError("Mask is empty or invalid.")

    x_min, x_max = x_coords[0], x_coords[-1]
    y_min, y_max = y_coords[0], y_coords[-1]

    # Box dimensions in pixels
    box_width_pixels = x_max - x_min
    box_height_pixels = y_max - y_min

    # Estimate depth in pixels using the diagonal of the ArUco marker
    # aruco_diagonal_pixels = np.linalg.norm(aruco_corners[0] - aruco_corners[2])
    depth_pixels = (box_width_pixels + box_height_pixels) / 2  # Approximate depth as average dimension

    # Convert depth to cm
    depth_cm = depth_pixels * scale

    return depth_cm


def estimate_volumen2(frame, bboxes, masks, aruco_size_cm = 3.5  ):
    # Detect ArUco marker
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, parameters)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    corners, ids, rejected = detector.detectMarkers(gray)

    # aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50)
    # parameters = cv2.aruco.DetectorParameters_create()
    # corners, ids, rejected = cv2.aruco.detectMarkers(undistorted_image, aruco_dict, parameters=parameters)

    if ids is not None:
        # Assuming one marker is detected
        marker_corners = corners[0][0]  # Get the first detected marker corners
        pixel_width = np.linalg.norm(marker_corners[0] - marker_corners[1])  # Top edge length in pixels
        scale = aruco_size_cm / pixel_width  # cm per pixel

        # Detect the box (use YOLO and SAM results)
        
        (x1,y1), (x2,y2) = bboxes[0]
        mask = masks[0]

        # Compute box dimensions in pixels
        box_width_pixels = x2-x1
        box_height_pixels = y2-y1
        box_depth_pixels = estimate_depth(mask, corners, scale)

        # Convert to real-world dimensions
        box_width_cm = box_width_pixels * scale
        box_height_cm = box_height_pixels * scale
        box_depth_cm = box_depth_pixels * scale
        volume = box_width_cm*box_height_cm*box_depth_cm

        frame = draw_mask(frame, mask, color=COLORS[0])
        cv2.rectangle(frame, (0,0), (frame.shape[1], 50), (255,255,255), -1)
        cv2.putText(frame, f"w={box_width_cm:.02f}, h={box_height_cm:.02f}, d={box_depth_cm:.02f}, v={volume:.02f}", (10, 30), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,0), 1)
        return volume, box_width_cm, box_height_cm, box_depth_cm, frame
    return None, None, None, None, frame

# INPUT_VIDEO = 'video/20250105_025331.mp4'
INPUT_VIDEO = 0
BOX_MODEL, SAM_MODEL = load_models()
# CAMERA_DIMS, CAMERA_MATRIX, DIST_COEFF = load_calibration()
THRESHOLD = 0.4

def draw_mask(frame, mask, color, alpha=0.5):
    colored_mask = np.zeros_like(frame)
    colored_mask[mask == 1] = color
    return cv2.addWeighted(frame, 1, colored_mask, alpha, 0)

def get_bbox(frame):
    result = BOX_MODEL.predict(source=frame,conf=THRESHOLD, max_det=1, verbose=False)[0]
    bboxes = []
    if result.boxes is not None and len(result.boxes) == 1:
        x1,y1,x2,y2 = result.boxes[0].xyxy[0].tolist()
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color=(0,255, 0), thickness=1)
        p1 = (int(x1), int(y1))
        p2 = (int(x2), int(y2))
        bboxes = [(p1   ,  p2)]
    return bboxes, frame

def get_sam(frame, bboxes):
    r = SAM_MODEL(frame, bboxes=bboxes, verbose=False)
    masks = r[0].masks.data.cpu().numpy()
    
    # Plot contours for each mask
    # for mask, color in zip(masks, COLORS[:len(masks)]):
    #     frame = draw_mask(frame, mask, color=color)
    return masks, frame

def process_frame(frame):
    bboxes, frame = get_bbox(frame)
    if len(bboxes) > 0:
        masks, frame = get_sam(frame, bboxes)
        # try:
        volume, w, h, d, frame= estimate_volumen2(frame, bboxes, masks)
        # except: pass
    
    return frame

def main():
    cap = cv2.VideoCapture(INPUT_VIDEO)
    set_reslution(cap, 640, 360, 30)
    print("Press 'q' or 'ESC' to quit")
    
    try:
        while True:
            found, frame = cap.read()
            if found:
                # h, w = frame.shape[:2]
                # new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(CAMERA_MATRIX, DIST_COEFF, (w, h), 1, (w, h))
                # frame = cv2.undistort(frame, CAMERA_MATRIX, DIST_COEFF, None, new_camera_matrix)
                
                frame = process_frame(frame)
                cv2.imshow('Video', frame)
                
            # Check for 'q' or ESC press
            key = cv2.waitKey(10) & 0xFF
            if key == ord('q') or key == 27:
                break
            elif key == ord('s'):
                cv2.waitKey(-1)

    finally:
        # Release everything when done
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()