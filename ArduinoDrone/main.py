from kivy.app import App
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivy.properties import (
    NumericProperty, ReferenceListProperty, ObjectProperty
)
from kivy.vector import Vector
from kivy.clock import Clock
    
class DroneUI(App):
    def build(self):
        return Builder.load_file("ui.kv")
    
    def up(self):
        print("Going UP!")
        
    def left(self):
        print("Going LEFT")
    
    def right(self):
        print("Going RIGHT")
        
    def down(self):
        print("Going DOWN")


if __name__ == '__main__':
    DroneUI().run()