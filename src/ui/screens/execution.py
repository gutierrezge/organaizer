# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from typing import Optional
from uuid import uuid4, UUID
from kivy.clock import Clock
from kivymd.uix.textfield import MDTextField
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import  Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics.texture import Texture
from camera import DepthCamera
from config import Config
from clp import Clp3DBinPackingGenerator
import numpy as np
from .box_table import BoxTable
from .clp_table import ClpTable
from domain import Execution, Box, GeneratedClpPlan, Prediction
from log import logging


ExecutionScreen_KV = """
<ExecutionScreen>:
    MDBoxLayout:
        id: root_layout
        orientation: 'horizontal'
        padding: 0
        spacing: 0
        
        MDBoxLayout:
            id: main_layout
            orientation: "vertical"
            padding: dp(20)
            spacing: dp(20)
            width: dp(680)
            size_hint_x: None
            
            MDBoxLayout:
                orientation: 'horizontal'
                padding: 0
                spacing: 50

                MDBoxLayout
                    id: containers_dimension_layout
                    orientation: 'vertical'
                    size_hint: None, None
                    size: dp(640), dp(240)
                    spacing: dp(30)
                    padding: 0
                    post_hint: {"center_y": 0.5}
                    
                    MDTextField:
                        id: container_width
                        text: root.container_width
                        on_text: root.container_width = self.text
                        mode: "rectangle"
                        hint_text: "Container's Width"
                        helper_text: "Enter the container's width in centimeters"
                        helper_text_mode: "on_focus"
                
                    MDTextField:
                        id: container_height
                        text: root.container_height
                        on_text: root.container_height = self.text
                        mode: "rectangle"
                        hint_text: "Container's Height"
                        helper_text: "Enter the container's height in centimeters"
                        helper_text_mode: "on_focus"

                    MDTextField:
                        id: container_depth
                        text: root.container_depth
                        on_text: root.container_depth = self.text
                        mode: "rectangle"
                        hint_text: "Container's Depth"
                        helper_text: "Enter the container's depth in centimeters"
                        helper_text_mode: "on_focus"
                    
            MDBoxLayout:
                id: video_layout
                orientation: "vertical"
                size_hint: None, None
                size: dp(640), dp(480)
                padding: 0
                spacing: 0

                Image:
                    id: video
                    size_hint: None, None
                    size: dp(640), dp(480)
                    post_hint: {"center_x": 0.5}
            
            MDBoxLayout:
                orientation: 'horizontal'
                padding: 0
                spacing: 150
                size_hint: None, None
                size: dp(640), dp(50)

                MDRaisedButton:
                    id: start_stop_camera_button
                    text: "Start Camera"
                    on_release: root.start_stop_camera()

                MDRaisedButton:
                    id: capture_image_button
                    text: "Capture"
                    disabled: True
                    on_release: root.capture_image()

                MDRaisedButton:
                    id: generate_clp_button
                    text: "Generate CLP"
                    disabled: True
                    on_release: root.generate_plan()
            
            MDBoxLayout:
                size_hint: None, 0.5
        
        MDBoxLayout:
            id: results_layout
            orientation: "vertical"
            size_hint: 1, 1
            padding: 0
            spacing: 10
            
            MDBoxLayout:
                id: boxes_layout
                orientation: "vertical"
                size_hint_y: None
                height: dp(550)

            MDBoxLayout:
                id: clp_layout
                orientation: "vertical"
                size_hint: 1, 1
                height: dp(550)
        
"""

class ExecutionScreen(Screen):
    container_width = StringProperty('200.0')
    container_height = StringProperty('200.0')
    container_depth = StringProperty('200.0')
    execution:Execution = ObjectProperty(Execution(id=uuid4(), container_width=200, container_height=200, container_depth=200))
    latest_prediction:Optional[Prediction] = None
    clp_remarks:Label = None
    capturing_video:bool = False
    
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.config = Config()
        self.camera = DepthCamera(self.config)
        self.clp_plan_generator = Clp3DBinPackingGenerator()

        self.box_table = BoxTable(remove_row_callback=self.on_box_table_remove_row)
        self.clp_table = ClpTable()

        self.ids.boxes_layout.add_widget(
            Label(
                text="Predicted Boxes",
                color=(0, 0, 0, 1),
                bold=True,
                valign="middle",
                halign="center",
                size_hint_y=None,
                height=dp(30),
            )
        )
        self.ids.boxes_layout.add_widget(self.box_table)

        self.ids.clp_layout.add_widget(
            Label(
                text="Container Loading Plan",
                color=(0, 0, 0, 1),
                bold=True,
                valign="middle",
                halign="center",
                size_hint_y=None,
                height=dp(30),
            )
        )
        self.ids.clp_layout.add_widget(self.clp_table)

        self.clp_remarks = Label(
            text="",
            color=(1, 0, 0, 1),
            bold=True,
            valign="middle",
            halign="left",
            size_hint_y=None,
            height=dp(30),
        )
        self.ids.clp_layout.add_widget(self.clp_remarks)


    def on_container_width(self, instance:MDTextField, value:str):
        if self.execution:
            try:
                self.execution.container_width = float(value)
            except: pass
            
    
    def on_container_height(self, instance:MDTextField, value:str):
        if self.execution:
            try:
                self.execution.container_height = float(value)
            except: pass
    
    def on_container_depth(self, instance:MDTextField, value:str):
        if self.execution:
            try:
                self.execution.container_depth = float(value)
            except: pass
        

    def on_pre_enter(self, *args):
        self.reset_data()
        self.video = self.ids.video
        return super().on_pre_enter(*args)
    
    def start_stop_camera(self):
        self.capturing_video = not self.capturing_video
        self.ids.capture_image_button.disabled = not self.capturing_video
        
        if self.capturing_video:
            self.ids.start_stop_camera_button.text = "Stop Camera"
            self.video = self.ids.video
            Clock.schedule_once(self.start_video_capture)
        else:
            self.camera.stop_camera()
            self.ids.start_stop_camera_button.text = "Start Camera"
            w, h = self.camera.config.camera.resolution
            texture = Texture.create(size=self.camera.config.camera.resolution, colorfmt='bgr')
            texture.blit_buffer(np.zeros((h, w, 3), dtype=np.uint8).tobytes(), colorfmt='bgr', bufferfmt='ubyte')
            self.video.texture = texture

    
    def start_video_capture(self, dt):
        if self.capturing_video and self.camera.open_camera():
            Clock.schedule_once(self.update_video_panel)

    def on_pre_leave(self, *args):
        self.camera.stop_camera()
        return super().on_pre_leave(*args)
    
    def update_video_panel(self, dt):
        try:
            self.latest_prediction = self.camera.read()
            if self.latest_prediction is not None:
                texture = Texture.create(size=self.camera.config.camera.resolution, colorfmt='bgr')
                texture.blit_buffer(self.latest_prediction.painted_frame.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
                texture.flip_vertical()
                self.video.texture = texture
        except:
            logging.error("Error processing camera", exc_info=True)
        finally:
            Clock.schedule_once(self.update_video_panel)

    def on_box_table_remove_row(self, table:BoxTable, short_id:UUID):
        self.execution.boxes = [b for b in self.execution.boxes if b.short_id != short_id]
        self.update_gallery()


    def reset_data(self):
        self.latest_prediction = None


    def to_texture(self, frame:np.ndarray):
        texture = Texture.create(size=[frame.shape[1], frame.shape[0]], colorfmt='bgr')
        texture.blit_buffer(frame.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
        texture.flip_vertical()
        return texture


    def capture_image(self):
        if self.latest_prediction is not None and self.latest_prediction.is_complete():
            box = Box(
                id=self.latest_prediction.id,
                execution_id=self.execution.id,
                frame=self.latest_prediction.painted_frame,
                x1=self.latest_prediction.bbox[0],
                y1=self.latest_prediction.bbox[1],
                x2=self.latest_prediction.bbox[2],
                y2=self.latest_prediction.bbox[3],
                width=self.latest_prediction.dimensions.side3.value,
                height=self.latest_prediction.dimensions.side4.value,
                depth=self.latest_prediction.dimensions.side5.value
            )
            self.execution.boxes.append(box)
            self.update_gallery()


    def update_gallery(self):
        self.box_table.set_rows([
            {
                "index": str(int(i)),
                "box_id": box.short_id,
                "box_width": f"{box.width:.02f}",
                "box_height": f"{box.height:.02f}",
                "box_depth": f"{box.depth:.02f}",
                "box_volume": f"{box.volume:.02f}",
                "frame_texture": self.to_texture(box.frame),
            } for i, box in enumerate(self.execution.boxes)
        ])
        self.ids.generate_clp_button.disabled = len(self.execution.boxes) == 0


    def image_removed(self, box:Box):
        index = None
        for i, b in enumerate(self.execution.boxes):
            if b.id == box.id:
                index = i
                break

        if index is not None:
            del self.execution.boxes[index]
            self.update_gallery()


    def generate_plan(self):
        if len(self.execution.boxes) > 0:
            plan: GeneratedClpPlan = self.clp_plan_generator.generate(self.execution)
            self.clp_remarks.text = plan.remarks
            
            clp_rows = [{
                "index": str(int(i)),
                "box_id": item.short_id,
                "box_x": f"{item.x:.02f}",
                "box_y": f"{item.y:.02f}",
                "box_z": f"{item.z:.02f}",
                "box_p": f"{item.image}"
            } for i, item in enumerate(plan.plan)]
            self.clp_table.set_rows(clp_rows)