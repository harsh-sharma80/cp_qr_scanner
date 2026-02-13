from kivy.config import Config

# Set default window size
Config.set('graphics', 'width', '675')
Config.set('graphics', 'height', '1500')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.camera import Camera
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage

from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout


from kivy.graphics import Color, Rectangle

from kivy.clock import Clock
from kivy.core.window import Window

from pyzbar import pyzbar
from PIL import Image
import requests
from datetime import datetime
import textwrap
import json


# your deployed Google Apps Script URL
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwYpIBV7AuNCdovwmpRRLNPADmvkWEIKElOdhRqvE3X0nEr7e37RLTDB6jY4yFqdkyn/exec"


class QRScanner(FloatLayout):
    #init function
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.orientation = "vertical"
        with self.canvas.before:
            Color(0.267, 0.267, 0.267, 1.0)  
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_bg, pos=self.update_bg)

        self.apps_script_url = None  # API link

        # Camera widget (Android-safe)
        self.camera = Camera(
            resolution=(800, 600),
            play=True,
            size_hint=(1,0.5),
            pos_hint={'x':0, 'y':0.3}
        )
        self.add_widget(self.camera)

        # Logo
        self.logo = KivyImage(source="clublogo.png",  size_hint=(0.2,0.2), pos_hint={'x':0.0, 'top':1})  # top-left corner
        self.add_widget(self.logo)

        # Label
        self.label = Label(
            text="Ready to Scan",
            color = (1,1,1,1),    #white
            size_hint=(1, 0.2),
            pos_hint={'x':0,'y':0.1},
            font_size=22
        )
        self.add_widget(self.label)

        # Start button
        self.start_btn = Button(
            text="Start Scanning",
            color = (1,1,1,1),    #white
            size_hint=(0.5, 0.1),
            pos_hint={"x":0.25,"y":0.02},
            background_normal='',
            background_color=(0, 0.5, 1, 1))

        self.start_btn.bind(on_press=self.start_scanning)
        self.add_widget(self.start_btn)

        # API Link button
        self.link_btn = Button(
            text="Set API Link",
            size_hint=(0.15, 0.04),
            pos_hint={"x":0.03, "y":0.26},
            background_normal='',
            background_color=(0, 0.5, 1, 1)
        )

        self.link_btn.bind(on_press=self.open_link_popup)
        self.add_widget(self.link_btn)

        # Send All Data button
        self.send_all_btn = Button(
            text="Transfer",
            size_hint=(0.1, 0.04),
            pos_hint={"x":0.86, "y":0.8},
            background_normal='',
            background_color=(0.2, 0.7, 0.2, 1)
        )

        self.send_all_btn.bind(on_press=self.send_all_data)
        self.add_widget(self.send_all_btn)

        self.last_qr = None
        self.scanning_event = None  # Store Clock event so we can start/stop


    # TAKING INPUT FOR API LINK
    def open_link_popup(self, instance):
        # FloatLayout for popup content
        layout = FloatLayout()

        # Text input
        self.link_input = TextInput(
            hint_text="<Google Apps Script URL>",
            multiline=False,
            size_hint=(0.9, 0.6),
            pos_hint={'x':0.05, 'y':0.3}
        )
        layout.add_widget(self.link_input)

        # Save button
        save_btn = Button(
            text="Save",
            size_hint=(0.9, 0.3),
            pos_hint={'x':0.05, 'y':0.1},
            background_normal='',
            background_color=(0, 0.5, 1, 1)
        )
        layout.add_widget(save_btn)

        # Close button (top-right)
        close_btn = Button(
            text="X",
            size_hint=(0.1, 0.1),
            pos_hint={'x':0.9, 'y':1},
            background_normal='',
            background_color=(1, 0, 0, 1)
        )
        layout.add_widget(close_btn)

        # Create popup
        popup = Popup(
            title="Set Google API Link",
            content=layout,
            size_hint=(0.6, 0.2)
        )

        # Bind buttons
        save_btn.bind(on_press=lambda x: self.save_link(popup))
        close_btn.bind(on_press=lambda x: popup.dismiss())

        # Open popup
        popup.open()



    # SAVING LINK TO BACKEND
    def save_link(self, popup):
        link = self.link_input.text.strip()

        if link.startswith("https://"):
            self.apps_script_url = link
            self.label.text = "API Link Set Successfully"
            self.label.color = (0, 1, 0, 1)
        else:
            self.label.text = "Invalid URL"
            self.label.color = (1, 0, 0, 1)

        popup.dismiss()



    # SEND DATA
    def send_all_data(self, instance):
        if not self.apps_script_url:
            self.label.text = "API URL Not Set"
            self.label.color = (1, 0, 0, 1)
            return

        try:
            with open("qr_output.jsonl", "r") as f:
                lines = f.readlines()

            if not lines:
                self.label.text = "No Data To Send"
                self.label.color = (1, 1, 0, 1)
                return

            data_list = [json.loads(line.strip()) for line in lines]

            self.label.text = "Sending data..."
            self.label.color = (1, 1, 1, 1)
            from kivy.clock import Clock
            Clock.tick()  # force UI refresh

            # Send entire file at once
            response = requests.post(
                self.apps_script_url,
                json={"bulk_data": data_list}
            )

            if response.status_code == 200:
                self.label.text = "Data Transfer Completed"
                self.label.color = (0, 1, 0, 1)

                # Clear file after success
                open("qr_output.jsonl", "w").close()
            else:
                self.label.text = "Upload Failed"
                self.label.color = (1, 0.5, 0, 1)

        except FileNotFoundError:
            self.label.text = "No Local File Found"
            self.label.color = (1, 0, 0, 1)

        except Exception as e:
            self.label.text = "Error Sending Data"
            self.label.color = (1, 0, 0, 1)
            print("Error:", e)


    # UPDATE BACKGROUND
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    
    #VERIFIES JSON -> expected QR format -> {"Key1":"vae1","Key2":"value2"}
    def is_valid_json_qr(self, data):
        required_fields = ["Name", "Roll", "Email"] 
        return isinstance(data, dict) and all(field in data for field in required_fields) 
    

    # START SCANNING FOR QR
    def start_scanning(self, instance):
        if self.scanning_event:
            # Stop scanning
            Clock.unschedule(self.scanning_event)
            self.scanning_event = None
            self.label.text = "Scanning stopped"
            color = (1,1,1,1)    #white
            self.label.color = (1,1,1,1)    #white
            self.start_btn.text = "Scan Again"
        else:
            # Start scanning
            self.label.text = "Point at QR code"
            self.label.color = (1,1,1,1)    #white
            self.scanning_event = Clock.schedule_interval(self.scan_qr, 0.5)
            self.start_btn.text = "Stop Scanning"   


    # QR READING
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

        try:
            qr_data = json.loads(qr_text)
        except json.JSONDecodeError:
            self.label.text = "Invalid QR format"
            self.label.color = (1, 0, 0, 1)
            return

        # Validate required fields
        if not self.is_valid_json_qr(qr_data):
            self.label.text = "QR missing values"
            self.label.color = (1, 0, 0, 1)
            return
        
        # Prevent duplicate scans
        timestamp = datetime.now().isoformat()

        # Check for today's duplicate entry
        if self.already_scanned_today(qr_data):
            self.label.text = "Duplicate Entry"
            self.label.color = (1, 0, 0, 1)  # red
            return

        self.send_to_file(qr_data, timestamp)

        # Pause scanning briefly
        Clock.unschedule(self.scan_qr)
        Clock.schedule_once(self.resume_scanning, 2)


    # START SCANNING AGAIN
    def resume_scanning(self, dt):
        self.label.text = "Point camera at QR code"
        self.label.color = (1,1,1,1)    #white
        if self.scanning_event:
            self.scanning_event = Clock.schedule_interval(self.scan_qr, 0.5)


    # AVOID DUPLICATE ENTRIES
    def already_scanned_today(self, qr_data):
        today = datetime.now().date().isoformat()
        roll = qr_data.get("Roll")

        try:
            with open("qr_output.jsonl", "r") as f:
                for line in f:
                    saved = json.loads(line)
                    saved_date = saved.get("timestamp", "").split("T")[0]
                    saved_roll = saved.get("Roll")

                    if saved_date == today and saved_roll == roll:
                        return True
        except FileNotFoundError:
            return False

        return False


    # SAVE DATA TO FILE
    def send_to_file(self, qr_data, timestamp):
        try:
            qr_data["timestamp"] = timestamp  # add timestamp

            with open("qr_output.jsonl", "a") as f:
                f.write(json.dumps(qr_data) + "\n")

            self.label.text = f"Saved:\n{qr_data.get('Name')}"
            self.label.color = (0, 1, 0, 1)

        except Exception as e:
            self.label.text = "File Error"
            self.label.color = (1, 0, 0, 1)
            print("Error:", e)


class QRApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        return QRScanner()


if __name__ == "__main__":
    QRApp().run()
