
import tkinter


class histogram(tkinter.Frame):

    def __init__(self, master=None, label="Undefined"):
        tkinter.Frame.__init__(self, master)
        self.master = master
        self.label = tkinter.Label(self, text=label, anchor="w")
        self.label.pack(side="top", fill="x")
        master.update()
        self.w = master.winfo_width()
        self.h = master.winfo_height()
        print(self.w)
        print(self.h)

    def update(self):
        self.w = master.winfo_width()
        self.h = master.winfo_height()
        print(self.w)
        print(self.h)
        self.master.update()