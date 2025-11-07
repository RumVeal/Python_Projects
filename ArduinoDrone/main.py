from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.uix.button import Button

    
class DroneUI(App):
    count_on_off = 0
    
    def build(self):
        return Builder.load_file("ui.kv")
    
    def forward(self):
        print("Going FORWADR")
        
    def left(self):
        print("Going LEFT")
    
    def right(self):
        print("Going RIGHT")
        
    def backward(self):
        print("Going BACKWARD")
    
    def on_off(self, button):
        if self.count_on_off == 0:
            print("ON")
            self.count_on_off = 1
            button.text = "ON"
            button.btn_color = (0, 0.7, 0, 1)
        else:
            print("OFF")
            button.text = "OFF"
            button.btn_color = (0.7, 0, 0, 1)
            self.count_on_off = 0
            
    def up(self):
        print("UP")
        
    def down(self):
        print("DOWN")
        
    def side_panel(self):
        panel = self.root.ids.side_panel
        
        if panel.x >= self.root.width:
            Animation(x=self.root.width - panel.width, d=0.25).start(panel)
        else:
            Animation(x=self.root.width, d=0.25).start(panel)
    
    def menu_info(self):
        panel = self.root.ids.side_panel
        info = self.root.ids.menu_content

        new_box = FloatLayout(
            size_hint=(None, None),
            pos=(panel.x, panel.y),
            size=(panel.width, panel.height)
        )
        
        with new_box.canvas.before:
            Color(0.12, 0.12, 0.14, 1)   # rgba
            rect = Rectangle(pos=new_box.pos, size=new_box.size)
        
        new_box.bind(pos=lambda *a: setattr(rect, 'pos', new_box.pos))
        new_box.bind(size=lambda *a: setattr(rect, 'size', new_box.size))
        
        lbl = Label(
            text="Information",
            color=(1,1,1,1),
            font_size=min(panel.width, panel.height) * 0.15,
            pos_hint={"center_x": 0.5, "center_y": 0.9}
        )
        
        lbl.bind(texture_size=lbl.setter("size"))

        
        back_btn = Button(
            text="Back",
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.1},
            background_normal="",
            background_color=(0.2, 0.6, 1, 0),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(texture_size=back_btn.setter("size"))
        back_btn.bind(on_release=self.menu_back)
        
        new_box.add_widget(lbl)
        new_box.add_widget(back_btn)
        
        info.add_widget(new_box)
        
    def menu_contact(self):
        panel = self.root.ids.side_panel
        info = self.root.ids.menu_content

        new_box = FloatLayout(
            size_hint=(None, None),
            pos=(panel.x, panel.y),
            size=(panel.width, panel.height)
        )
        
        with new_box.canvas.before:
            Color(0.12, 0.12, 0.14, 1)   # rgba
            rect = Rectangle(pos=new_box.pos, size=new_box.size)
        
        new_box.bind(pos=lambda *a: setattr(rect, 'pos', new_box.pos))
        new_box.bind(size=lambda *a: setattr(rect, 'size', new_box.size))
        
        lbl = Label(
            text="Contact",
            color=(1,1,1,1),
            font_size=min(panel.width, panel.height) * 0.15,
            pos_hint={"center_x": 0.5, "center_y": 0.9}
        )
        lbl.bind(texture_size=lbl.setter("size"))

        
        back_btn = Button(
            text="Back",
            size_hint=(None, None),
            pos_hint={"center_x": 0.5, "center_y": 0.1},
            background_normal="",
            background_color=(0.2, 0.6, 1, 0),
            color=(1, 1, 1, 1)
        )
        back_btn.bind(texture_size=back_btn.setter("size"))
        back_btn.bind(on_release=self.menu_back)
        
        new_box.add_widget(lbl)
        new_box.add_widget(back_btn)
        
        info.add_widget(new_box)

    def menu_back(self, instance):
        info = self.root.ids.menu_content
        info.clear_widgets()
        


if __name__ == '__main__':
    DroneUI().run()