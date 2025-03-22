# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager
from ui.screens.execution import ExecutionScreen, ExecutionScreen_KV

class ExecutionApp(MDApp):
    def build(self):
        Window.maximize()
        self.title = "Organaizer"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        
        Builder.load_string(ExecutionScreen_KV)
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(ExecutionScreen(name="execution"))

        return self.screen_manager


if __name__ == "__main__":
    ExecutionApp().run()