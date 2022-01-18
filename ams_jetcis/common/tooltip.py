import tkinter as tk

class CreateToolTip(object):
    def __init__(self, widget, widget_frame, text='widget info'):
        self.widget = widget
        self.widget_frame = widget_frame
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None
        self.mouse_in_widget = False

    def set_text(self, text):
        self.text = text

    def enter(self, event=None):
        self.mouse_in_widget = True
        self.widget_frame.after(1000, self.make_tip)


    def make_tip(self):
        if (self.mouse_in_widget == True) and (self.tw == None):
            x = y = 0
            x, y, cx, cy = self.widget.bbox("insert")
            x += 8 + self.widget.winfo_pointerx()
            y += 5 + self.widget.winfo_pointery()

            # creates a toplevel window
            self.tw = tk.Toplevel(self.widget)

            # Leaves only the label and removes the app window
            self.tw.wm_overrideredirect(True)
            self.tw.wm_geometry("+%d+%d" % (x, y))
            label = tk.Label(self.tw, text=self.text, justify='left',
                           background='white', relief='solid', borderwidth=1)
            label.pack(ipadx=1)
            label.after(2000, self.close)

    def close(self, event=None):
        self.mouse_in_widget = False
        if self.tw:
            self.tw.destroy()
        self.tw = None