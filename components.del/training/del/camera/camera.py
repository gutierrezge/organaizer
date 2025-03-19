# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


import cv2
import time
import numpy as np
import pyrealsense2 as rs
from typing import Optional
from . import CameraConfig
from detection.box import BoxDetection
from detection.models import Prediction
from skimage.restoration import denoise_wavelet
from components.training.del.log import logging
from collections import deque

class Camera:


    def __init__(self):
        self.config:CameraConfig = CameraConfig()

        self.detection = BoxDetection(
            ".data/runs/train/organaizer4/weights/best.pt",
            "sam2_t.pt",
            self.config
        )


    def open_camera(self):
        self.cap = cv2.VideoCapture(self.config.camera_id)
        if not self.cap.isOpened():
            return False
        self.__set_reslution__()
        return True


    def is_open(self):
        return self.cap is not None and self.cap.isOpened()


    def stop_camera(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.cap = None


    def __set_reslution__(self):
        if self.is_open():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)


    def read(self) -> Optional[Prediction]:
        if self.is_open():
            found, frame = self.cap.read()
            if found:
                return self.detection.predict(frame)
        return None


class DepthCamera:


    def __init__(self):
        self.config:CameraConfig = CameraConfig()
        self.detection = BoxDetection(
            ".data/runs/train/organaizer4/weights/best.pt",
            "sam2_t.pt",
            self.config
        )
        self.pipeline = None
        self.depth_intrinsics = None
        self.distance_estimator = None
        self.align = None
        self.color_images = deque(maxlen=self.config.frame_buffer)
        self.depth_matrices = deque(maxlen=self.config.frame_buffer)


    def open_camera(self):
        try:
            self.pipeline:rs.pipeline = rs.pipeline()
            
            config = rs.config()
            config.disable_all_streams()
            config.enable_stream(rs.stream.depth, self.config.resolution[0], self.config.resolution[1], rs.format.z16, self.config.fps)
            config.enable_stream(rs.stream.color, self.config.resolution[0], self.config.resolution[1], rs.format.bgr8, self.config.fps)
            
            pipeline_profile = self.pipeline.start(config)
            self.align = rs.align(rs.stream.color)
            self.depth_intrinsics:rs.intrinsics = rs.video_stream_profile(pipeline_profile.get_stream(rs.stream.depth)).get_intrinsics()
            
            self.detection.init(self.depth_intrinsics)
            return True
        except:
            logging.error("Unable to open camera", exc_info=True)

        return False


    def is_open(self):
        return self.pipeline is not None


    def stop_camera(self):
        try:
            if self.pipeline:
                self.pipeline.stop()
        except:
            pass
        self.pipeline = None
        self.depth_intrinsics = None
        self.distance_estimator = None
        self.align = None
        self.color_images.clear()
        self.depth_matrices.clear()


    def get_enhanced_color_image(self, images):
        return np.clip(np.mean(np.array(images, dtype=np.float32), axis=0), 0, 255).astype(np.uint8)


    def get_enhanced_depth_frame(self, depths):
        return denoise_wavelet(np.mean(depths.copy(), axis=0), method='BayesShrink', mode='soft', rescale_sigma=True)


    def read(self) -> Optional[Prediction]:
        while True:
            try:
                frames:rs.composite_frame = self.pipeline.wait_for_frames(timeout_ms=1000)
                if frames:
                    depth_frame = frames.get_depth_frame()
                    color_frame = frames.get_color_frame()

                    if not depth_frame or not color_frame:
                        logging.warning("Depth and Color frame not found.")
                        return None

                    frames = self.align.process(frames)
                    depth_frame = frames.get_depth_frame()
                    color_frame = frames.get_color_frame()

                    if not depth_frame or not color_frame:
                        logging.warning("Depth and Color frame not found after alignment.")
                        return None
                    
                    self.color_images.append(np.asanyarray(color_frame.get_data()).copy())
                    self.depth_matrices.append(np.asanyarray(depth_frame.get_data()).copy())

                    color_frame = self.get_enhanced_color_image(self.color_images)
                    depth_frame = self.get_enhanced_depth_frame(self.depth_matrices)

                    return self.detection.predict(color_frame, depth_frame)
                logging.warning("Frames are None")
                return None
            except:
                logging.error("Unable to capture frames.", exc_info=True)
                self.restart_camera()

    def restart_camera(self) -> bool:
        self.stop_camera()
        time.sleep(5)
        return self.open_camera()