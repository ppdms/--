import rumps
import datetime
import json
import os
from AppKit import NSApplication, NSApplicationActivationPolicyAccessory

class Stopwatch(rumps.App):
    def __init__(self):
        super(Stopwatch, self).__init__("⏱️")
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        self.start_time = None
        self.stopwatch_active = False
        self.config_file = os.path.expanduser('~/.stopwatch_state.json')
        self.load_state()
        self.start_stopwatch_thread()

    def load_state(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    if data.get('active'):
                        self.start_time = datetime.datetime.fromisoformat(data['start_time'])
                        self.stopwatch_active = True
        except Exception:
            self.start_time = None
            self.stopwatch_active = False

    def save_state(self):
        data = {
            'active': self.stopwatch_active,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f)

    @rumps.clicked('Toggle')
    def toggle_stopwatch(self, _):
        if not self.stopwatch_active:
            self.start_time = datetime.datetime.now()
            self.stopwatch_active = True
        else:
            self.start_time = None
            self.stopwatch_active = False
            self.title = "⏱️"
        self.save_state()

    def format_time(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

    def start_stopwatch_thread(self):
        @rumps.timer(1)
        def update_stopwatch(_):
            if self.stopwatch_active and self.start_time:
                diff = datetime.datetime.now() - self.start_time
                total_seconds = diff.seconds
                
                # If more than 24 hours have passed, reset the stopwatch
                if diff.days > 0:
                    self.start_time = None
                    self.stopwatch_active = False
                    self.title = "⏱️"
                    self.save_state()
                else:
                    self.title = self.format_time(total_seconds)

if __name__ == "__main__":
    Stopwatch().run()
