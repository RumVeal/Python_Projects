from kivy.app import App
from kivy.lang import Builder

    
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
        

if __name__ == '__main__':
    DroneUI().run()