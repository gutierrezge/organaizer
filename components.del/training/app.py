# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

import cv2
import numpy as np
import pyrealsense2 as rs
from skimage.restoration import denoise_wavelet
import traceback
from collections import deque


def reset_hardware() -> None:
    for dev in rs.context().query_devices():
        dev.hardware_reset()


def get_config(resolution) -> rs.config:
    config = rs.config()
    config.disable_all_streams()
    config.enable_stream(rs.stream.depth, resolution[0], resolution[1], rs.format.z16, resolution[2])
    config.enable_stream(rs.stream.color, resolution[0], resolution[1], rs.format.bgr8, resolution[2])
    return config


def close_camera(pipeline) -> None:
    try:
        pipeline.stop()
    except: pass


def main():
    frame_buffer = 10
    color_frames = deque(maxlen=frame_buffer)
    depth_frames = deque(maxlen=frame_buffer)
    
    resolution=[640,360, 30]
    
    pipeline = None
    align = None

    try:
        while True:
            if pipeline is None:
                print("Openning depth camera ....")
                reset_hardware()
                
                pipeline = rs.pipeline()
                pipeline.start(get_config(resolution))
                align = rs.align(rs.stream.color)

            try:
                frames = pipeline.wait_for_frames(timeout_ms=1000)
            except: continue
            if not frames: continue
                
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame: continue

            frames = align.process(frames)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame()
            if not depth_frame or not color_frame: continue

            color_frame = np.asanyarray(color_frame.get_data()).copy()
            depth_frame = np.asanyarray(depth_frame.get_data()).copy()
            
            color_frames.append(color_frame)
            depth_frames.append(depth_frame)
            
            color_frame = np.clip(np.mean(np.array(color_frames, dtype=np.float32), axis=0), 0, 255).astype(np.uint8)
            depth_frame = denoise_wavelet(np.mean(depth_frames, axis=0), method='BayesShrink', mode='soft', rescale_sigma=True)

            depth_frame = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame, alpha=0.15), cv2.COLORMAP_RAINBOW)
            frame = np.hstack((color_frame, depth_frame))
            
            cv2.imshow('Frame', frame)
            key = cv2.waitKey(5)
            if key == ord('q'):
                break
    except Exception as e:
        print(f"Failed to grab frames. {str(e)}")
        traceback.print_exc()
    finally:
        print("Cleaning up resources....")
        cv2.destroyAllWindows()
        close_camera(pipeline)


if __name__ == "__main__":
    main()