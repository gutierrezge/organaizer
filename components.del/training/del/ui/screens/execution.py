# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from typing import List, Optional
from kivy.clock import Clock
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.textfield import MDTextField
from kivy.properties import StringProperty, ObjectProperty
from kivy.uix.screenmanager import  Screen
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from camera.camera import DepthCamera
from ui.components.card import HoverImageCard
from kivy.metrics import dp
from detection.models import Prediction, GeneratedClpPlan
from clp.clp import ClpPlanGenerator
from dao import ExecutionDAO
from components.training.del.log import logging


ExecutionScreen_KV = """
<ExecutionScreen>:
    MDBoxLayout:
        id: main_layout
        orientation: "vertical"
        padding: dp(10)
        
        GridLayout:
            id: header_layout
            cols: 3
            size_hint_y: 0.25
            padding: 0

            AsyncImage:
                source: "assets/organaizer.png"
                size_hint: (None, None)
                size: dp(50), dp(50)
            Label:
                text: "New Executions"
                color: (0, 0, 0, 1)
                bold: True
                font_size: "18sp"
            MDIconButton:
                icon: "close"
                on_release: root.go_back()

        GridLayout:
            id: containers_dimension_layout
            cols: 3
            size_hint_y: 0.3
            padding: 0, dp(10), 0, dp(10)
            spacing: dp(20)
            
            MDTextField:
                id: container_width
                mode: "rectangle"
                hint_text: "Container's Width"
                helper_text: "Enter the container's width in centimeters"
                helper_text_mode: "on_focus"
        
            MDTextField:
                id: container_height
                mode: "rectangle"
                hint_text: "Container's Height"
                helper_text: "Enter the container's height in centimeters"
                helper_text_mode: "on_focus"

            MDTextField:
                id: container_depth
                mode: "rectangle"
                hint_text: "Container's Depth"
                helper_text: "Enter the container's depth in centimeters"
                helper_text_mode: "on_focus"

        GridLayout:
            id: video_gallery_layout
            cols: 2

            MDBoxLayout:
                id: video_layout
                orientation: "vertical"
                size_hint: None, None
                size: dp(350), dp(260)
                padding: dp(5)
                spacing: dp(5)
                        
                Label:
                    text: "Video Feed"
                    color: (0, 0, 0, 1)
                    bold: True
                    valign: "middle"
                    halign: "center"
                    size_hint_x: None
                    width: dp(350)
                Image:
                    id: video
                    size_hint: None, None
                    size: dp(320), dp(180)
                    pos_hint: {"center_x": 0.5}

                MDRaisedButton:
                    text: "Capture"
                    pos_hint: {"center_x": 0.5}
                    size_hint: None, None
                    size: dp(120), dp(40)
                    on_release: root.capture_image()

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
                    
        MDBoxLayout:
            id: results_layout
            orientation: "horizontal"
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

class ExecutionScreen(Screen):
    title = StringProperty("New Execution")
    execution = ObjectProperty(None)
    captured_predictions:List[Prediction] = []
    latest_prediction:Optional[Prediction] = None
    clp_remarks:Label = None
    
    def __init__(self, dao:ExecutionDAO, **kwargs):
        Screen.__init__(self, **kwargs)
        self.dao = dao
        self.camera = DepthCamera()
        self.clp_plan_generator = ClpPlanGenerator()

        self.ids.container_width.bind(text=self.on_text_change)
        self.ids.container_height.bind(text=self.on_text_change)
        self.ids.container_depth.bind(text=self.on_text_change)

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
                ("ID", dp(25)),
                ("Width", dp(25)),
                ("Height", dp(25)),
                ("Depth", dp(25)),
                ("Volume", dp(25))
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


    def on_text_change(self, text_field:MDTextField, value:str):
        """Allows only numbers with up to 2 decimal places."""
        try:
            if '.' in value:
                parts = value.split('.')
                if len(parts) == 2 and len(parts[1]) > 2:
                    text_field.text = text_field.text[:-1]
            try:
                float(value)
            except ValueError:
                text_field.text = text_field.text[:-1]
        finally:
            self.process_images()



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
                texture = Texture.create(size=self.camera.config.resolution, colorfmt='bgr')
                texture.blit_buffer(self.latest_prediction.painted_frame.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
                texture.flip_vertical()
                self.video.texture = texture
        except:
            logging.error("Error processing camera", exc_info=True)
        finally:
            Clock.schedule_once(self.update_video_panel)

    def reset_data(self):
        self.execution = None
        self.captured_predictions = []
        self.latest_prediction = None
        self.clp_data_table.row_data = []
        self.boxes_data_table.row_data = []
        self.ids.container_width.text = ""
        self.ids.container_depth.text = ""
        self.ids.container_height.text = ""
        gallery = self.ids.gallery_layout
        gallery.clear_widgets()


    def go_back(self,):
        self.reset_data()
        self.manager.current = "home"
        

    def capture_image(self):
        if self.latest_prediction is not None:
            self.captured_predictions.append(self.latest_prediction)
            self.update_gallery()

    def update_gallery(self):
        gallery = self.ids.gallery_layout
        gallery.clear_widgets()

        for prediction in self.captured_predictions:
            gallery.add_widget(HoverImageCard(prediction, self.image_removed))
        
        self.process_images()

    def image_removed(self, prediction:Prediction):
        index = None
        for i, pred in enumerate(self.captured_predictions):
            if pred.id == prediction.id:
                index = i
                break

        if index is not None:
            del self.captured_predictions[index]
            self.update_gallery()

    def get_containers_dimension(self):
        w,h,d = 0, 0, 0
        try:
            w = float(self.ids.container_width.text)
        except:
            pass
        try:
            h = float(self.ids.container_height.text)
        except:
            pass
        try:
            d = float(self.ids.container_depth.text)
        except:
            pass

        return w, h, d

    def process_images(self):
        self.boxes_data_table.row_data = [
            (pred.short_id, f"{pred.dimensions.width:.02f}", f"{pred.dimensions.height:.02f}", f"{pred.dimensions.depth:.02f}", f"{pred.dimensions.volume:.02f}")
            for pred in self.captured_predictions
        ]
        w, h, d = self.get_containers_dimension()
        plan: GeneratedClpPlan = self.clp_plan_generator.generate(w, h, d, self.captured_predictions)
        self.clp_remarks.text = plan.remarks
        
        self.clp_data_table.row_data = [
            (item.short_id, f"{item.x:02f}", f"{item.y:02f}", f"{item.x:02f}")
            for item in plan.plan
        ]
        
    def _find_next_widget(self):
        widgets = [w for w in self.walk() if isinstance(w, MDTextField)]
        try:
            current_index = widgets.index(Window.focus)
            return widgets[(current_index + 1) % len(widgets)]
        except:
            return widgets[0] if widgets else None
