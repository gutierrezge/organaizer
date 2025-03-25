from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from typing import Callable
from kivy.properties import StringProperty, NumericProperty, ObjectProperty



KV = '''
<BoxRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(64)
    spacing: dp(10)
    padding: dp(5)

    Button:
        text: "View"
        size_hint_x: 0.1
        on_release: root.open_popup()

    Image:
        texture: root.frame_texture
        size_hint_x: 0.1
        size: dp(48), dp(48)

    Label:
        text: root.box_id
        size_hint_x: 0.1
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1

    Label:
        text: root.box_width
        size_hint_x: 0.1
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1

    Label:
        text: root.box_height
        size_hint_x: 0.1
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1
    
    Label:
        text: root.box_depth
        size_hint_x: 0.1
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1
    
    Label:
        text: root.box_volume
        size_hint_x: 0.1
        size_hint_y: None
        height: dp(48)
        halign: 'left'
        valign: 'middle'
        color: 0, 0, 0, 1

    Button:
        text: "Remove"
        size_hint_x: 0.1
        on_release: root.parent.parent.parent.remove_row(root.index)


<BoxTable>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(10)

    BoxLayout:
        size_hint_y: None
        height: dp(32)
        spacing: dp(10)
        padding: dp(5)

        Label:
            text: "[b]View[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Image[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Box Id[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Side 1[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Side 2[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Side 3[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

        Label:
            text: "[b]Volume[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1
        
        Label:
            text: "[b]Action[/b]"
            markup: True
            size_hint_x: 0.1
            color: 0, 0, 0, 1

    RecycleView:
        id: rv
        viewclass: 'BoxRow'
        RecycleBoxLayout:
            default_size: None, dp(64)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
'''

Builder.load_string(KV)


class BoxRow(BoxLayout):
    index = NumericProperty()
    box_id = StringProperty()
    box_width = StringProperty()
    box_height = StringProperty()
    box_depth = StringProperty()
    box_volume = StringProperty()
    frame_texture = ObjectProperty()

    def open_popup(self):
        popup = Popup(
            title=f"Box Image - ID: {self.box_id}",
            content=Image(texture=self.frame_texture),
            size_hint=(0.5, 0.5),
        )
        popup.open()



class BoxTable(BoxLayout):


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