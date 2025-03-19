import cv2
import numpy as np
from typing import Dict, List, Tuple

class CameraCalibrator:
    def __init__(self, camera_id: int = 0, pattern_size: Tuple[int, int] = (8, 6), 
                 resolution: Tuple[int, int] = (800, 600)):
        """
        Initialize the camera calibrator
        Args:
            camera_id: ID of the camera to use
            pattern_size: Size of the chessboard pattern (inner corners)
            resolution: Desired camera resolution (width, height)
        """
        self.camera_id = camera_id
        self.pattern_size = pattern_size
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        
        # Initialize camera
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera_id}")
            
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        
        # Verify the actual resolution
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        # Get frame size
        _, frame = self.cap.read()
        self.frame_size = frame.shape[:2]
        
        # Prepare object points
        self.objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
        
        # Storage for calibration images
        self.calibration_frames: List[np.ndarray] = []

    def set_reslution(self, cap, w, h, fps):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        cap.set(cv2.CAP_PROP_FPS, fps)

        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
        print(f"Actual: {actual_width}x{actual_height} at {actual_fps}")
        return actual_width, actual_height, actual_fps
        
    def detect_chessboard(self, frame: np.ndarray) -> Tuple[bool, np.ndarray]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        display_frame = frame.copy()
        
        ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
        
        if ret:
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
            display_frame= cv2.drawChessboardCorners(display_frame, self.pattern_size, corners2, ret)
            
        return ret, display_frame
            
    def calibrate(self) -> Dict:
        if not self.calibration_frames:
            raise RuntimeError("No calibration frames collected")
            
        objpoints = []
        imgpoints = []
        
        for frame in self.calibration_frames:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
            
            if ret:
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                objpoints.append(self.objp)
                imgpoints.append(corners2)
        
        if not objpoints:
            raise RuntimeError("No valid calibration patterns found in collected frames")
            
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None
        )
        
        if not ret:
            raise RuntimeError("Calibration failed")
            
        return {
            'fx': float(mtx[0, 0]),
            'fy': float(mtx[1, 1]),
            'cx': float(mtx[0, 2]),
            'cy': float(mtx[1, 2]),
            'dist_coeffs': dist.tolist()
        }
    
    def run_calibration_session(self):
        print("Press 's' to save a calibration frame")
        print("Press 'c' to perform calibration")
        print("Press 'q' to quit without calibrating")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            # Detect and display chessboard
            found, display_frame = self.detect_chessboard(frame)
            
            # Show number of collected frames
            text = f"Collected frames: {len(self.calibration_frames)} - Res: {self.actual_width}x {self.actual_height}, FPS: {self.actual_fps}"
            cv2.rectangle(display_frame, (0,0), (display_frame.shape[1], 20), (255,255,255), -1)
            cv2.putText(display_frame, text, (10, 15), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (0, 255, 0) if found else (0, 0, 255), 1)
            
            cv2.imshow('Calibration', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                if found:
                    self.calibration_frames.append(frame)
                    print(f"Saved frame {len(self.calibration_frames)}")
                else:
                    print("No chessboard detected - frame not saved")
                    
            elif key == ord('c'):
                if len(self.calibration_frames) < 10:
                    print("Please collect at least 10 frames before calibrating")
                    continue
                    
                try:
                    intrinsics = self.calibrate()
                    print("\nCalibration successful!")
                    print("\nCamera Intrinsics:")
                    print(f"fx: {intrinsics['fx']:.2f}")
                    print(f"fy: {intrinsics['fy']:.2f}")
                    print(f"cx: {intrinsics['cx']:.2f}")
                    print(f"cy: {intrinsics['cy']:.2f}")
                    print("\nDistortion Coefficients:")
                    print(f"{intrinsics['dist_coeffs']}")
                    break
                    
                except Exception as e:
                    print(f"Calibration failed: {e}")
                    
            elif key == ord('q'):
                print("Quitting without calibration")
                break
                
        self.cap.release()
        cv2.destroyAllWindows()
        
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'cap'):
            self.cap.release()

if __name__ == "__main__":
    try:
        calibrator = CameraCalibrator()
        calibrator.run_calibration_session()
    except Exception as e:
        print(f"Error: {e}")