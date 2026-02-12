from kivy.config import Config
Config.set('graphics', 'width', '640')
Config.set('graphics', 'height', '480')
Config.set('graphics', 'resizable', '1')
Config.set('kivy', 'log_level', 'debug')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera

class CameraTest(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"

        # Force OpenCV provider
        self.camera = Camera(
            play=True,
            index=0,
            resolution=(640, 480),
            # Kivy will pick opencv automatically if installed
        )
        self.add_widget(self.camera)

class CamApp(App):
    def build(self):
        return CameraTest()

if __name__ == "__main__":
    CamApp().run()
