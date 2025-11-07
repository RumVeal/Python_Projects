from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.metrics import dp

    
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
    
    def menu(self):
        panel = self.root.ids.menu_content

        new_box = BoxLayout(
            orientation="horizontal",
            size_hint=(1, None),
            height=dp(40),
            spacing=dp(5)
        )

        new_box.add_widget(Label(
            text="New Item",
            color=(1,1,1,1),
            font_size=min(Window.width, Window.height) * 0.018
        ))

        panel.add_widget(new_box)


if __name__ == '__main__':
    DroneUI().run()