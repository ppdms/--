import rumps
import datetime
from dateutil.relativedelta import relativedelta
import json
import os
import objc
from AppKit import (NSWindow, NSTitledWindowMask, NSBackingStoreBuffered,
    NSDatePickerElementFlagYearMonthDay, NSDatePickerElementFlagHourMinuteSecond,
    NSCenterTextAlignment, NSApplication, NSApplicationActivationPolicyAccessory,
    NSFont, NSAttributedString, NSDictionary, NSDate, NSMakeRect, NSDatePicker,
    NSButton, NSObject, NSBezelStyleRounded
)

class Stopwatch(rumps.App):
    def __init__(self):
        super(Stopwatch, self).__init__("⏱️")
        NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        self.stopwatch_epoch = None
        self.target_date = None
        self.config_file = os.path.expanduser('~/.stopwatch_state.json')
        self.window = None
        self.date_picker = None
        self.date_selector_window = None
        self.day_progress_enabled = None
        self.stopwatch_enabled = None
        self.date_comparison_enabled = None
        self.days_only_date_comparison = None
        self.YMD_date_comparison = None
        self.load_state()
        self.menu.add(rumps.MenuItem('Disable Day Progress' if self.day_progress_enabled else 'Enable Day Progress', callback=self.toggle_day_progress))
        self.menu.add(rumps.MenuItem('Disable Stopwatch' if self.stopwatch_enabled else 'Enable Stopwatch', callback=self.toggle_stopwatch))
        self.menu.add(rumps.MenuItem('Disable Date Comparison' if self.date_comparison_enabled else 'Enable Date Comparison', callback=self.toggle_date_comparison))
        self.menu.add(rumps.MenuItem('Toggle Date Comparison Format (D)' if self.days_only_date_comparison else ('Toggle Date Comparison Format (YMD)' if self.YMD_date_comparison else 'Toggle Date Comparison (YMDHMS)'), callback=self.toggle_date_comparison_format))
        rumps.Timer(self.update_display, 1).start()

    def load_state(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                self.date_comparison_enabled = data.get('date_comparison_enabled')
                self.day_progress_enabled = data.get('day_progress_enabled')
                self.stopwatch_enabled = data.get('stopwatch_enabled')
                self.stopwatch_epoch = datetime.datetime.fromisoformat(data.get('stopwatch_epoch')) if data.get('stopwatch_epoch') else None
                self.target_date = datetime.datetime.fromisoformat(data.get('target_date')) if data.get('target_date') else None
                self.days_only_date_comparison = data.get('days_only_date_comparison') 
                self.YMD_date_comparison = data.get('YMD_date_comparison')
    
    def save_state(self):
        data = {
            'date_comparison_enabled': self.date_comparison_enabled,
            'day_progress_enabled': self.day_progress_enabled,
            'stopwatch_enabled': self.stopwatch_enabled,
            'stopwatch_epoch': self.stopwatch_epoch.isoformat() if self.stopwatch_epoch else None,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'days_only_date_comparison': self.days_only_date_comparison,
            'YMD_date_comparison': self.YMD_date_comparison
        }
        with open(self.config_file, 'w') as f:
            json.dump(data, f)

    def toggle_stopwatch(self, sender):
        if self.stopwatch_enabled:
            self.stopwatch_enabled = False
            self.stopwatch_epoch = None
            sender.title = "Enable Stopwatch"
        else:
            self.stopwatch_enabled = True
            self.stopwatch_epoch = datetime.datetime.now()
            sender.title = "Disable Stopwatch"
        self.save_state()

    def toggle_day_progress(self, sender):
        if self.day_progress_enabled:
            self.day_progress_enabled = False
            sender.title = 'Enable Day Progress'
        else:
            self.day_progress_enabled = True
            sender.title = 'Disable Day Progress'
        self.save_state()

    def toggle_date_comparison(self, sender):
        if self.date_comparison_enabled:
            self.date_comparison_enabled = False
            sender.title = 'Enable Date Comparison'
        else:
            self.date_comparison_enabled = True
            sender.title = 'Disable Date Comparison'
            if self.date_selector_window is None:
                self.date_selector_window = DatePickerWindowController.alloc().initWithCallback_(self.handle_date_set)
            self.date_selector_window.showWindow()
        self.save_state()
    
    def toggle_date_comparison_format(self, sender):
        if self.days_only_date_comparison:
            self.days_only_date_comparison = False
            self.YMD_date_comparison = True
            sender.title = 'Toggle Date Comparison Format (YMD)'
        elif self.YMD_date_comparison:
            self.YMD_date_comparison = False
            sender.title = 'Toggle Date Comparison Format (YMDHMS)'
        else:
            self.days_only_date_comparison = True
            sender.title = 'Toggle Date Comparison Format (D)'
        self.save_state()

    def set_monospace_title(self, title_text):
        if hasattr(self._nsapp, 'nsstatusitem'):
            font = NSFont.monospacedSystemFontOfSize_weight_(14, 0.0)
            attributes = NSDictionary.dictionaryWithObject_forKey_(font, "NSFont")
            attributed_title = NSAttributedString.alloc().initWithString_attributes_(
                title_text, attributes
            )
            self._nsapp.nsstatusitem.setAttributedTitle_(attributed_title)

    def update_display(self, _=None):
        MenuText = "⏱️" if not (self.day_progress_enabled or self.stopwatch_enabled or self.date_comparison_enabled) else ""

        if self.day_progress_enabled:
            now = datetime.datetime.now()
            seconds = 3600 * now.hour + 60 * now.minute + now.second
            if seconds >= 22 * 60 * 60 or seconds < 6 * 60 * 60:
                MenuText += "😴" if MenuText == "" else " | 😴"
            else:
                percentage = (100 * (seconds - 6 * 60 * 60)) / (16 * 60 * 60)
                MenuText += f"{percentage:.2f}%" if MenuText == "" else f" | {percentage:.2f}%"
        if self.stopwatch_enabled:
            if self.stopwatch_epoch:
                diff = datetime.datetime.now() - self.stopwatch_epoch
                total_seconds = diff.seconds
                
                # If more than 24 hours have passed, reset the stopwatch
                if (diff.days > 0):
                    self.stopwatch_epoch = None
                    self.stopwatch_enabled = None
                    self.save_state()
                else:
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    secs = total_seconds % 60

                    if hours > 0:
                        formatted_time = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                    else:
                        formatted_time = f"{minutes:02d}:{secs:02d}"
                    
                    MenuText += formatted_time if MenuText == "" else f" | {formatted_time}"
            else:
                self.stopwatch_epoch = None
                self.stopwatch_enabled = None
                self.save_state()

        if self.date_comparison_enabled:
            if self.target_date:
                if type(self.target_date).__name__ == "__NSTaggedDate":
                    self.target_date = datetime.datetime.fromtimestamp(self.target_date.timeIntervalSince1970())
                    self.save_state()
                rd = relativedelta(self.target_date, datetime.datetime.now())
                duration = ""
                if self.days_only_date_comparison:
                    duration += str((datetime.datetime.now() - self.target_date).days) + "D"
                else:
                    if rd.years: duration += f"{abs(rd.years)}Y "
                    if rd.months: duration += f"{abs(rd.months)}M "
                    if rd.days: duration += f"{abs(rd.days)}D"
                    if self.YMD_date_comparison == False:
                        duration += f" {abs(rd.hours):02}:{abs(rd.minutes):02}:{abs(rd.seconds):02}"
                MenuText += "" if duration == "" else (duration if MenuText == "" else f" | {duration}")

        self.set_monospace_title(MenuText)

    @objc.python_method
    def handle_date_set(self, date):
        self.target_date = date

class DatePickerWindowController(NSObject):
    window = objc.ivar('window')
    date_picker = objc.ivar('date_picker')
    callback = objc.ivar('callback')
    
    def initWithCallback_(self, callback):
        self = objc.super(DatePickerWindowController, self).init()
        if self is None: return None
        
        self.callback = callback
        self.setupWindow()
        return self
        
    def setupWindow(self):
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 350, 250),
            NSTitledWindowMask,
            NSBackingStoreBuffered,
            False
        )
        self.window.setTitle_("Set Target Date")
        self.window.center()
        
        date_picker = NSDatePicker.alloc().initWithFrame_(NSMakeRect(25, 70, 300, 150))
        date_picker.setDatePickerStyle_(1)
        date_picker.setDatePickerElements_(NSDatePickerElementFlagYearMonthDay | 
                                         NSDatePickerElementFlagHourMinuteSecond)
        date_picker.setBezeled_(True)
        date_picker.setDrawsBackground_(True)
        date_picker.setAlignment_(NSCenterTextAlignment)
        date_picker.setDateValue_(NSDate.date())
        
        self.window.contentView().addSubview_(date_picker)
        self.date_picker = date_picker

        set_button = NSButton.alloc().initWithFrame_(NSMakeRect(125, 20, 100, 30))
        set_button.setTitle_("Set Time")
        set_button.setTarget_(self)
        set_button.setAction_(objc.selector(self.buttonClicked))
        set_button.setBezelStyle_(NSBezelStyleRounded)
        self.window.contentView().addSubview_(set_button)

    def showWindow(self):
        self.window.center()
        self.window.setLevel_(3)
        self.window.makeKeyAndOrderFront_(None)

    @objc.IBAction
    def buttonClicked(self, sender):
        target_date = self.date_picker.dateValue()
        self.callback(target_date)
        self.window.orderOut_(None)

if __name__ == "__main__":
    Stopwatch().run()
