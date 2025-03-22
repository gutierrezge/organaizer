# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp
import numpy as np
from domain import Box


class HoverImageCard(MDCard):

    def __init__(self, box:Box, frame:np.ndarray, on_delete_callback, **kwargs):
        super().__init__(**kwargs)
        self.box = box
        self.on_delete_callback = on_delete_callback
        divider = 2
        size = (int(frame.shape[1]/divider), int(frame.shape[0]/divider))
        self.size_hint = (None, None)
        self.size = size
        self.radius = [5]
        self.padding = 2
        self.elevation = 1

        # Create RelativeLayout for the image and delete button
        layout = RelativeLayout()
        self.add_widget(layout)

        # Add Image
        img = Image(
            source="placeholder.jpg",
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size=size
        )
        
        texture = Texture.create(size=[frame.shape[1], frame.shape[0]], colorfmt='bgr')
        texture.blit_buffer(frame.tobytes(), colorfmt='bgr', bufferfmt='ubyte')
        texture.flip_vertical()
        img.texture = texture
        layout.add_widget(img)
        layout.add_widget(Label(
            text=box.short_id,
            color = (0,0,0,1),
            pos_hint={'center_x': 0.5, 'center_y': 0}
        ))

        # Add "X" button
        close_button = MDIconButton(
            icon="close",
            icon_size=dp(15),
            pos_hint={"right": 1, "top": 1},
            md_bg_color = (255, 255, 255, 0.5)
        )
        close_button.bind(on_release=lambda instance: self.on_delete())
        layout.add_widget(close_button)


    def on_delete(self, *args):
        self.on_delete_callback(self.box)
