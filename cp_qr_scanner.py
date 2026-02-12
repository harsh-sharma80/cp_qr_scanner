#testing on pc
from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')



from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage

from kivy.clock import Clock
from kivy.core.window import Window

from pyzbar import pyzbar
from PIL import Image
import requests
from datetime import datetime
import textwrap



# your deployed Google Apps Script URL
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwYpIBV7AuNCdovwmpRRLNPADmvkWEIKElOdhRqvE3X0nEr7e37RLTDB6jY4yFqdkyn/exec"


class QRScanner(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"

        # Camera widget (Android-safe)
        self.camera = Camera(
            resolution=(800, 600),
            play=True,
            size_hint=(1,1),
            pos_hint={'x':0, 'y':0.16}
        )
        self.add_widget(self.camera)

        # Logo
        self.corner_img = KivyImage(source="clublogo.png",  
                                size_hint=(None, None),
                                size = (80,80),
                                pos_hint={'x':0.0, 'top':1})  # top-left corner
        self.add_widget(self.corner_img)

        # Status labela
        self.label = Label(
            text="Ready to Scan",
            size_hint=(1, 0.2),
            pos_hint={'x':0,'y':0.1},
            font_size=22
        )
        self.add_widget(self.label)

        # Start scanning button
        self.start_btn = Button(text="Start Scanning", size_hint=(1, 0.1))
        self.start_btn.bind(on_press=self.start_scanning)
        self.add_widget(self.start_btn)

        self.last_qr = None
        self.scanning_event = None  # Store Clock event so we can start/stop


    def start_scanning(self, instance):
        if self.scanning_event:
            # Stop scanning
            Clock.unschedule(self.scanning_event)
            self.scanning_event = None
            self.label.text = "Scanning stopped"
            self.start_btn.text = "Scan"
        else:
            # Start scanning
            self.label.text = "Point at QR code"
            self.scanning_event = Clock.schedule_interval(self.scan_qr, 0.5)
            self.start_btn.text = "Stop Scanning"    

    def scan_qr(self, dt):
        texture = self.camera.texture
        if not texture:
            return

        # Convert camera texture to image
        image = Image.frombytes(
            mode="RGBA",
            size=texture.size,
            data=texture.pixels
        )

        decoded = pyzbar.decode(image)
        if not decoded:
            return

        qr_text = decoded[0].data.decode("utf-8")

        # Prevent duplicate scans
        if qr_text == self.last_qr:
            self.label.text = f"Same as last saved QR"
            return

        self.last_qr = qr_text
        timestamp = datetime.now().isoformat()

        self.label.text = f"Saving...\n{qr_text}"

        self.send_to_sheet(qr_text, timestamp)

        # Pause scanning briefly
        Clock.unschedule(self.scan_qr)
        Clock.schedule_once(self.resume_scanning, 2)

    def resume_scanning(self, dt):
        self.label.text = "Point camera at QR code"
        if self.scanning_event:
            self.scanning_event = Clock.schedule_interval(self.scan_qr, 0.5)




    #Data sharing to google sheet
    def send_to_sheet(self, qr_text, timestamp):
        try:
            with open("qr_output.txt", "a") as f:
                f.write(f"{timestamp} - {qr_text}\n")
            wrapped_text= "\n".join(textwrap.wrap(qr_text, width=20))
            self.label.text = f"Saved locally\n{wrapped_text}"
        except Exception as e:
            self.label.text = f"File error"
            print("Error writing QR:", e)


class QRApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        return QRScanner()


if __name__ == "__main__":
    QRApp().run()
