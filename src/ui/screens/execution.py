# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from typing import Optional
from uuid import uuid4
from kivy.clock import Clock
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.textfield import MDTextField
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import  Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics.texture import Texture
from ui.components.card import HoverImageCard
from camera import DepthCamera
from config import Config
from clp import ClpPlanGenerator
from domain import Execution, Box, GeneratedClpPlan, Prediction
import plot
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
                            
            MDRaisedButton:
                text: "Capture"
                on_release: root.capture_image()
            
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
                size_hint: 1, 1

            MDBoxLayout:
                id: clp_layout
                orientation: "vertical"
                size_hint: 1, 1
        
"""


"""
        GridLayout:
            id: video_gallery_layout
            cols: 2

            MDBoxLayout:
                id: gallery_container_layout
                orientation: "vertical"
                size_hint: 1, None
                height: dp(260)
                padding: dp(10)
                spacing: dp(10)

                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 1
                    Line:
                        width: dp(2)
                        rectangle: self.x + dp(10), self.y + dp(10), self.width - dp(20), self.height - dp(20)
                
                MDBoxLayout:
                    orientation: "horizontal"
                    size_hint: 1, None
                    height: dp(30)
                    padding: dp(10)

                    Label:
                        text: "Captured Images"
                        color: (0, 0, 0, 1)
                        bold: True
                        valign: "middle"
                        halign: "left"
                        size_hint_x: 0.5

                ScrollView:
                    bar_width: dp(12)
                    bar_color: 0.2, 0.6, 0.8, 1
                    bar_inactive_color: 0.6, 0.6, 0.6, 1
                    do_scroll_x: False
                    do_scroll_y: True
                    
                    GridLayout:
                        id: gallery_layout
                        cols: 2
                        size_hint_y: None
                        height: self.minimum_height
                        row_default_height: dp(180)
                        row_force_default: True
                        spacing: dp(5)
                        padding: dp(5)
                    
        

"""

class ExecutionScreen(Screen):
    container_width = StringProperty('0.0')
    container_height = StringProperty('0.0')
    container_depth = StringProperty('0.0')
    execution:Execution = ObjectProperty(Execution(id=uuid4()))
    latest_prediction:Optional[Prediction] = None
    clp_remarks:Label = None
    
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.config = Config()
        self.camera = DepthCamera(self.config)
        self.clp_plan_generator = ClpPlanGenerator()

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
        self.boxes_data_table = MDDataTable(
            use_pagination=False,
            check=False,
            elevation=0,
            column_data=[
                ("Id", dp(60)),
                ("Image", dp(30)),
                ("Width", dp(30)),
                ("Height", dp(30)),
                ("Depth", dp(30)),
                ("Volume", dp(30))
            ],
            row_data=[]
        )

        self.ids.boxes_layout.add_widget(self.boxes_data_table)

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
        self.clp_data_table = MDDataTable(
            use_pagination=False,
            check=False,
            elevation=0,
            column_data=[
                ("ID", dp(25)),
                ("X", dp(25)),
                ("Y", dp(25)),
                ("Z", dp(25))
            ],
            row_data=[]
        )
        self.ids.clp_layout.add_widget(self.clp_data_table)

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
                self.generate_plan()
            except: pass
            
    
    def on_container_height(self, instance:MDTextField, value:str):
        if self.execution:
            try:
                self.execution.container_height = float(value)
                self.generate_plan()
            except: pass
    
    def on_container_depth(self, instance:MDTextField, value:str):
        if self.execution:
            try:
                self.execution.container_depth = float(value)
                self.generate_plan()
            except: pass
        

    def on_pre_enter(self, *args):
        self.reset_data()
        self.video = self.ids.video
        Clock.schedule_once(self.start_video_capture)
        return super().on_pre_enter(*args)
    
    def start_video_capture(self, dt):
        if self.camera.open_camera():
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

    def reset_data(self):
        self.latest_prediction = None
        self.clp_data_table.row_data = []
        self.boxes_data_table.row_data = []
        # gallery = self.ids.gallery_layout
        # gallery.clear_widgets()


    def capture_image(self):
        if self.latest_prediction is not None:
            box = Box(
                id=self.latest_prediction.id,
                execution_id=self.execution.id,
                frame=self.latest_prediction.painted_frame,
                x1=self.latest_prediction.bbox[0],
                y1=self.latest_prediction.bbox[1],
                x2=self.latest_prediction.bbox[2],
                y2=self.latest_prediction.bbox[3],
                width=self.latest_prediction.dimensions.width,
                height=self.latest_prediction.dimensions.height,
                depth=self.latest_prediction.dimensions.depth
            )
            self.execution.boxes.append(box)
            self.update_gallery()


    def update_gallery(self):
        # gallery = self.ids.gallery_layout
        # gallery.clear_widgets()

        # for box in self.execution.boxes:
        #     gallery.add_widget(HoverImageCard(box, box.frame, self.image_removed))
        
        self.generate_plan()


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
        self.boxes_data_table.row_data = [
            (box.short_id, f"{box.width:.02f}", f"{box.height:.02f}", f"{box.depth:.02f}", f"{box.volume:.02f}")
            for box in self.execution.boxes
        ]
        plan: GeneratedClpPlan = self.clp_plan_generator.generate(self.execution)
        self.clp_remarks.text = plan.remarks
        
        self.clp_data_table.row_data = [
            (item.short_id, f"{item.x:02f}", f"{item.y:02f}", f"{item.x:02f}")
            for item in plan.plan
        ]
