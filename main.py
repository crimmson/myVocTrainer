import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import datetime

FILE = "phrases.xlsx"

df = pd.read_excel(FILE)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Apprentissage FR ↔ DE")

        self.themes = sorted(df["themes"].unique())
        self.setup_menu()

    def setup_menu(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack()

        ttk.Label(frame, text="themes").pack()
        self.theme_var = tk.StringVar(value=self.themes[0])
        ttk.Combobox(frame, textvariable=self.theme_var, values=self.themes).pack()

        ttk.Label(frame, text="Nombre de phrases").pack()
        self.nb_var = tk.IntVar(value=10)
        ttk.Combobox(frame, textvariable=self.nb_var, values=[10,20,50]).pack()

        ttk.Label(frame, text="Sens").pack()
        self.dir_var = tk.StringVar(value="FR → DE")
        ttk.Combobox(frame, textvariable=self.dir_var, values=["FR → DE","DE → FR"]).pack()

        ttk.Button(frame, text="Démarrer", command=self.start).pack(pady=10)

    def start(self):
        theme = self.theme_var.get()
        n = self.nb_var.get()

        subset = df[df["themes"]==theme].copy()

        today = datetime.today()
        subset["weight"] = subset.apply(
            lambda r: (1/(r["score"]+1)) +
                      ((today - pd.to_datetime(r["last_review"])).days/30),
            axis=1
        )

        self.session = subset.sample(min(n,len(subset)), weights=subset["weight"]).index.tolist()
        self.index = 0

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_quiz()

    def setup_quiz(self):
        self.frame = ttk.Frame(self.root, padding=20)
        self.frame.pack()

        self.question = ttk.Label(self.frame, text="", font=("Arial",16))
        self.question.pack(pady=20)

        self.answer = ttk.Label(self.frame, text="", font=("Arial",14), foreground="gray")
        self.answer.pack(pady=10)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Afficher réponse", command=self.show_answer).grid(row=0,column=0,padx=5)
        ttk.Button(btn_frame, text="✔", command=self.correct).grid(row=0,column=1,padx=5)
        ttk.Button(btn_frame, text="❌", command=self.wrong).grid(row=0,column=2,padx=5)

        self.load_question()

    def load_question(self):
        if self.index >= len(self.session):
            self.question.config(text="Session terminée 🎉")
            self.answer.config(text="")
            df.to_excel(FILE, index=False)
            return

        self.row_id = self.session[self.index]
        row = df.loc[self.row_id]

        self.current = row
        direction = self.dir_var.get()

        if direction == "FR → DE":
            self.question.config(text=row["fr"])
        else:
            self.question.config(text=row["de"])

        self.answer.config(text="")

    def show_answer(self):
        direction = self.dir_var.get()
        if direction == "FR → DE":
            self.answer.config(text=self.current["de"])
        else:
            self.answer.config(text=self.current["fr"])

    def update_stats(self, success):
        if success:
            df.at[self.row_id,"score"] += 1
        else:
            df.at[self.row_id,"score"] = max(0, df.at[self.row_id,"score"] - 1)

        df.at[self.row_id,"last_review"] = datetime.today().strftime("%Y-%m-%d")

    def correct(self):
        self.update_stats(True)
        self.index += 1
        self.load_question()

    def wrong(self):
        self.update_stats(False)
        self.session.append(self.row_id)
        self.index += 1
        self.load_question()

root = tk.Tk()
App(root)
root.mainloop()