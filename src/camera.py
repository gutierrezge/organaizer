# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano


import time
import cv2
import numpy as np
import pyrealsense2 as rs
from typing import Optional
from detection.box import BoxDetection
from domain import Prediction
from log import logging
from collections import deque
from config import Config

class DepthCamera:


    def __init__(self, config:Config):
        self.config:Config = config
        self.detection = BoxDetection(config)
        self.pipeline = None
        self.depth_intrinsics = None
        self.distance_estimator = None
        self.align = None
        self.running = False
        self.depth_matrices = deque(maxlen=self.config.camera.frame_buffer)


    def open_camera(self):
        if not self.is_open():
            try:
                self.pipeline:rs.pipeline = rs.pipeline()
                
                config = rs.config()
                config.disable_all_streams()
                config.enable_stream(rs.stream.depth, self.config.camera.resolution[0], self.config.camera.resolution[1], rs.format.z16, self.config.camera.fps)
                config.enable_stream(rs.stream.color, self.config.camera.resolution[0], self.config.camera.resolution[1], rs.format.bgr8, self.config.camera.fps)
                
                pipeline_profile = self.pipeline.start(config)
                self.align = rs.align(rs.stream.color)
                self.depth_intrinsics:rs.intrinsics = rs.video_stream_profile(pipeline_profile.get_stream(rs.stream.depth)).get_intrinsics()
                
                self.detection.init(self.depth_intrinsics)
                self.running = True
                logging.info("Depth Camera openned.")
            except:
                self.running = False
                logging.error("Unable to open camera", exc_info=True)

        return self.running


    def is_open(self):
        return self.running


    def stop_camera(self):
        if self.is_open():
            try:
                if self.pipeline:
                    self.pipeline.stop()
            except:
                pass
            self.pipeline = None
            self.depth_intrinsics = None
            self.distance_estimator = None
            self.align = None
            self.depth_matrices.clear()


    def get_enhanced_color_image(self, image:np.ndarray):
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        enhanced_lab = cv2.merge((l, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)


    def get_enhanced_depth_frame(self, depths):
        return np.mean(depths, axis=0)


    def read(self) -> Optional[Prediction]:
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
                
                color_frame = np.asanyarray(color_frame.get_data()).copy()
                depth_frame = np.asanyarray(depth_frame.get_data()).copy()
                self.depth_matrices.append(depth_frame)

                return self.detection.predict(color_frame, depth_frame)
            logging.warning("Frames are None")
        except:
            logging.error("Unable to capture frames.", exc_info=True)

        return None

    def restart_camera(self) -> bool:
        self.stop_camera()
        time.sleep(5)
        return self.open_camera()