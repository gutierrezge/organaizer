# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivy.lang import Builder
from ui.screens.home import HomeScreen
from ui.screens.execution import ExecutionScreen, ExecutionScreen_KV
from kivy.core.window import Window
from dao import ExecutionDAO
from components.training.del.log import logging


class ExecutionApp(MDApp):
    def build(self):
        Window.size = (1280, 720)
        self.title = "Organaizer"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.dao = ExecutionDAO()

        Builder.load_string(ExecutionScreen_KV)
        self.screen_manager = ScreenManager()
        self.home_screen = HomeScreen(self.dao, name="home")
        self.execution_screen = ExecutionScreen(self.dao, name="execution")

        self.screen_manager.add_widget(self.home_screen)        
        self.screen_manager.add_widget(self.execution_screen)

        return self.screen_manager


    

if __name__ == "__main__":
    ExecutionApp().run()