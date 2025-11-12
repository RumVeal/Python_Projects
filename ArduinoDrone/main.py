from kivy.app import App
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.properties import StringProperty
from kivy.storage.jsonstore import JsonStore
import os
    
class DroneUI(App):
    count_on_off = 0
    pid_value = StringProperty("")
    
    def build(self):
        self.store = JsonStore(os.path.join(self.user_data_dir, "settings.json"))
        if self.store.exists("pid"):
            self.pid_value = self.store.get("pid")["value"]
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
    
    def info_panel(self):
        info_panel = self.root.ids.info_panel
        side_panel = self.root.ids.side_panel
        
        if info_panel.x >= self.root.width:
            Animation(x=self.root.width - info_panel.width, d=0.25).start(info_panel)
        if side_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(side_panel)
        
    def contact_panel(self):
        contact_panel = self.root.ids.contact_panel
        side_panel = self.root.ids.side_panel
        
        if contact_panel.x >= self.root.width:
            Animation(x=self.root.width - contact_panel.width, d=0.25).start(contact_panel)
        if side_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(side_panel)
    
    def back_button(self):
        info_panel = self.root.ids.info_panel
        side_panel = self.root.ids.side_panel
        contact_panel = self.root.ids.contact_panel
        
        if contact_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(contact_panel)
        
        if info_panel.x < self.root.width:
            Animation(x=self.root.width, d=0.25).start(info_panel)
        if side_panel.x >= self.root.width:
            Animation(x=self.root.width - side_panel.width, d=0.25).start(side_panel)

    def menu_back(self, instance):
        info = self.root.ids.menu_content
        info.clear_widgets()
        
    def save_pid(self, text):
        self.pid_value = text
        self.store.put("pid", value=text)




if __name__ == '__main__':
    DroneUI().run()