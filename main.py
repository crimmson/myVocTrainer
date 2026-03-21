import tkinter as tk
from data import load_data
from ui import App

df = load_data()

root = tk.Tk()
App(root, df)
root.mainloop()