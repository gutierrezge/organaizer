from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from typing import Callable
from kivy.properties import StringProperty, NumericProperty


KV = '''
<ClpRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(64)
    spacing: dp(10)
    padding: dp(5)

    Label:
        text: root.box_id
        size_hint_x: 0.25
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1

    Label:
        text: root.box_x
        size_hint_x: 0.25
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1

    Label:
        text: root.box_y
        size_hint_x: 0.25
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1
    
    Label:
        text: root.box_z
        size_hint_x: 0.25
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1


<ClpTable>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(32)
        spacing: dp(10)
        padding: dp(5)

        Label:
            text: "[b]Box Id[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]X[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Y[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Z[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

    RecycleView:
        id: rv
        viewclass: 'ClpRow'
        RecycleBoxLayout:
            default_size: None, dp(64)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
'''

Builder.load_string(KV)


class ClpRow(BoxLayout):
    index = NumericProperty()
    box_id = StringProperty()
    box_x = StringProperty()
    box_y = StringProperty()
    box_z = StringProperty()


class ClpTable(BoxLayout):


    def __init__(self, remove_row_callback:Callable=None, **kwargs):
        super().__init__(**kwargs)
        self.rows = []
        self.remove_row_callback = remove_row_callback


    def set_rows(self, data):
        self.rows = data
        self.refresh()


    def refresh(self):
        self.ids.rv.data = self.rows


    def remove_row(self, index):
        if self.remove_row_callback is not None:
            index = str(int(index))
            for row in self.rows:
                if row["index"] == index:
                    self.remove_row_callback(self, row["box_id"])