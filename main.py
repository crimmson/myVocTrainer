import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import datetime

FILE = "phrases.xlsx"

df = pd.read_excel(FILE)
df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce").astype("datetime64[ns]")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("MyVocTrainer")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        self.themes = sorted(df["themes"].unique())
        self.setup_menu()

    def setup_menu(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(expand=True)

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

    def compute_weight(self, row):

        today = pd.Timestamp.today()

        days = (today - row["last_review"]).days if pd.notna(row["last_review"]) else 999

        if row["status"] == "wrong":
            base = 5
        elif row["status"] == "new":
            base = 3
        else:
            base = 1

        return base + days/10

    def start(self):

        theme = self.theme_var.get()
        n = self.nb_var.get()
        self.errors_total = 0
        self.errors = []
        self.first_attempt = set()
        self.delay_repeat = 3
        self.repeat_queue = []

        subset = df[df["themes"]==theme].copy()

        subset["status"] = subset["status"].fillna("new")

        subset["last_review"] = pd.to_datetime(
            subset["last_review"],
            errors="coerce"
        )

        self.today = pd.Timestamp.today()

        subset["weight"] = subset.apply(self.compute_weight, axis=1)

        if subset["weight"].sum() == 0:
            subset["weight"] = 1

        self.session = subset.sample(min(n,len(subset)), weights=subset["weight"]).index.tolist()

        self.index = 0

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_quiz()

    def setup_quiz(self):
        self.frame = ttk.Frame(self.root, padding=20)
        self.frame.pack()

        self.counter_label = ttk.Label(self.frame, text="", font=("Arial",10))
        self.counter_label.pack()

        self.question = ttk.Label(self.frame, text="", font=("Arial",16), wraplength=450, justify="center")
        self.question.pack(pady=20)

        self.answer = ttk.Label(self.frame, text="", font=("Arial",14), foreground="gray", wraplength=450, justify="center")
        self.answer.pack(pady=10)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Afficher réponse", command=self.show_answer).grid(row=0,column=0,padx=5)
        ttk.Button(btn_frame, text="✔", command=self.correct).grid(row=0,column=1,padx=5)
        ttk.Button(btn_frame, text="❌", command=self.wrong).grid(row=0,column=2,padx=5)

        ttk.Button(self.frame, text="Quitter session", command=self.return_to_menu).pack(pady=15)

        self.load_question()

    def return_to_menu(self):
        df.to_excel(FILE, index=False)
        self.frame.destroy()
        self.setup_menu()

    def load_question(self):
        for item in list(self.repeat_queue):
            if item["due"] <= self.index:
                self.session.insert(self.index + 1, item["row"])
                self.repeat_queue.remove(item)
        
        if self.index >= len(self.session):
            if self.errors:
                self.session = self.errors
                self.errors = []
                self.index = 0
                return self.load_question()
            
            self.question.config(text="Session terminée 🎉")
            self.answer.config(text="")
            df.to_excel(FILE, index=False)

            for widget in self.frame.winfo_children():
                widget.destroy()

            ttk.Label(self.frame, text="Session terminée 🎉", font=("Arial",16)).pack(pady=20)
            ttk.Button(self.frame, text="Terminé", command=self.return_to_menu).pack()

            return

        self.row_id = self.session[self.index]
        row = df.loc[self.row_id]

        total = len(self.session)
        current = self.index + 1
        errors_left = len(self.errors)

        pending_repeats = len(self.repeat_queue)

        self.counter_label.config(
            text=f"{self.index+1}/{len(self.session)} | répétitions prévues: {pending_repeats}"
        )

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

        if self.row_id not in self.first_attempt:

            if success:
                df.at[self.row_id,"status"] = "correct"
            else:
                df.at[self.row_id,"status"] = "wrong"

            df.at[self.row_id,"last_review"] = pd.Timestamp.now().floor("s")

            self.first_attempt.add(self.row_id)

    def correct(self):
        self.update_stats(True)
        self.index += 1
        self.load_question()

    def wrong(self):
        self.update_stats(False)
        #self.errors.append(self.row_id)
        if not any(item["row"] == self.row_id for item in self.repeat_queue):
            self.repeat_queue.append({
                "row": self.row_id,
                "due": self.index + self.delay_repeat
            })
        self.index += 1
        self.errors_total += 1
        self.load_question()

root = tk.Tk()
App(root)
root.mainloop()