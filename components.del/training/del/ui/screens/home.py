# All rights reserved. No part of this code may be reproduced, distributed, or transmitted
# in any form or by any means, including photocopying, recording, or other electronic or
# mechanical methods, without the prior written permission of the author, except in the
# case of brief quotations embodied in critical reviews and certain other noncommercial
# uses permitted by copyright law. For permission requests, please contact the author.
#
# Copyright (c) Lucía Alejandra Moreno Canuto, Gabriel Ernesto Gutiérrez Añez, Alicia Hernández Gutiérrez, Guillermo Daniel González Lozano

from uuid import UUID
import json
from typing import List, Dict
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp
from dao import ExecutionDAO, Execution
from components.training.del.log import logging


class HomeScreen(Screen):
    
    title = StringProperty("Executions")

    def __init__(self, dao:ExecutionDAO, **kwargs):
        Screen.__init__(self, **kwargs)
        self.dao = dao
        self.executions_dict:Dict[UUID, Execution] = {}
        self.executions:List[Execution]
        self.to_delete_rows:List[UUID] = []

        layout = MDBoxLayout(
            orientation="vertical",
            spacing=dp(15)
        )

        # Header with logo and text
        toolbar_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(5), dp(5), dp(5), dp(5))
        )

        # Logo Image
        custom_icon_button = AsyncImage(
            source="assets/organaizer.png",
            size_hint=(None, 1),
            allow_stretch=True,
            keep_ratio=True
        )
        toolbar_layout.add_widget(custom_icon_button)

        # Header Label
        toolbar_layout.add_widget(Label(
            text="Executions",
            size_hint=(None, 1),
            size=(dp(100), dp(56)),
            color=(0, 0, 0, 1),
            bold=True,
            font_size="20sp",
            valign="middle",
            halign="left",
        ))
        layout.add_widget(toolbar_layout)

        table_conrol_layout = MDBoxLayout(
            orientation="horizontal",
            padding=(dp(30), dp(5), dp(30), dp(5)),
            size_hint=(1, None),
            height=dp(56),
            spacing=dp(10), 
        )

        # Button for New Execution
        new_execution_button = MDRaisedButton(
            text="Create New",
            theme_text_color="Primary",
            size_hint=(0.1, 1),
            on_release=self.create_new_execution,
        )
        
        # BUtton to Delete Executions
        self.delete_button = MDRaisedButton(
            text="Delete Selection",
            theme_text_color="Secondary",
            size_hint=(0.1, 1),
            on_release=self.delete_selected_executions
        )
        self.delete_button.set_disabled(True)
        

        # Filter text field
        self.filter_text_field = MDTextField(
            hint_text="Filter table",
            helper_text="Press enter to filter data",
            helper_text_mode="on_focus",
            mode="rectangle",
            size_hint=(0.8, None),
        )
        self.filter_text_field.bind(on_text_validate=self.filter_data)

        table_conrol_layout.add_widget(self.filter_text_field)
        table_conrol_layout.add_widget(self.delete_button)
        table_conrol_layout.add_widget(new_execution_button)

        # Table with data
        self.data_table = MDDataTable(
            size_hint=(1, 1),
            use_pagination=False,
            check=True,
            sorted_on="Created",
            sorted_order="DSC",
            elevation=0,
            column_data=[
                ("ID", dp(80)),
                ("Container Capacity (cm3)", dp(40)),
                ("Total Boxes", dp(30)),
                ("Boxes Vol (cm3)", dp(40)),
                ("Status", dp(20)),
                ("Created", dp(30))
            ],
            row_data=[]
        )
        self.data_table.bind(on_check_press=self.on_check_press)

        layout.add_widget(table_conrol_layout)
        layout.add_widget(self.data_table)
        
        self.add_widget(layout)


    def on_check_press(self, instance_table, current_row):
        execution_id = UUID(current_row[0])
        if execution_id not in self.to_delete_rows:
            self.to_delete_rows.append(execution_id)
        else:
            self.to_delete_rows.remove(execution_id)

        self.delete_button.set_disabled(len(self.to_delete_rows) == 0)



    def filter_data(self,  key=None):
        value = self.filter_text_field.text
        if len(value) > 2:
            filtered_data:List[Execution] = [
                self.executions_dict[UUID(data[0])]
                for data in self.data_table.row_data if value.upper() in json.dumps(data).upper()
            ]
            self.set_table_data(filtered_data)
        else:
            self.set_table_data(self.executions)


    def on_pre_enter(self, *args):
        self.refresh_table()

    def create_new_execution(self, instance):
        execution_screen = self.manager.get_screen("execution")
        execution_screen.title = "New Execution"
        self.manager.current = "execution"

    def view_execution(self, execution_id:UUID):
        execution_screen = self.manager.get_screen("execution")
        execution_screen.title = f"View Execution {execution_id}"
        execution_screen.execution = self.executions_dict[execution_id]
        self.manager.current = "execution"

    def delete_selected_executions(self, execution_id:UUID):
        deleted:List[UUID] = []
        for execution_id in self.to_delete_rows:
            if self.dao.delete(execution_id):
                deleted.append(execution_id)

        for execution_id in deleted:
            self.to_delete_rows.remove(execution_id)

        self.refresh_table()


    def refresh_table(self):
        self.executions =  self.dao.find_all()
        self.executions_dict = {
            e.id: e
            for e in self.executions
        }
        self.filter_data(None)


    def set_table_data(self, data:List[Execution]):
        self.data_table.row_data = [
            (
                str(e.id),
                f"{e.container_width*e.container_height*e.container_depth:.02f}",
                str(e.total_boxes),
                f"{e.total_volume:.02f}",
                str(e.status),
                e.created_on.strftime('%Y-%m-%d %H:%M%S')
            )
            for e in data
        ]

    def create_action_buttons(self, execution_id:Execution):
        # Create a container for the buttons
        container = MDBoxLayout(orientation="horizontal", spacing=5, size_hint_x=None, width=dp(60))

        # Add a delete button
        delete_button = MDIconButton(
            icon="delete",
            on_release=lambda x: self.delete_execution(execution_id.id),
        )
        container.add_widget(delete_button)

        # Add more buttons here if needed (e.g., view, edit)
        return container