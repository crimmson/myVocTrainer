import tkinter as tk
from tkinter import ttk
import pandas as pd
from datetime import datetime

FILE = "phrases.xlsx"

df = pd.read_excel(FILE)

df["last_review"] = pd.to_datetime(df["last_review"], errors="coerce").astype("datetime64[ns]")

# sécurité colonnes
if "interval" not in df.columns:
    df["interval"] = 1

if "next_review" not in df.columns:
    df["next_review"] = pd.Timestamp.today()

if "status" not in df.columns:
    df["status"] = "new"

# nettoyage des données
df["interval"] = pd.to_numeric(df["interval"], errors="coerce").fillna(1).astype(int)
df["interval"] = df["interval"].clip(upper=10)

df["next_review"] = pd.to_datetime(df["next_review"], errors="coerce")

class App:
    def __init__(self, root):
        
        

        self.root = root
        self.root.title("MyVocTrainer")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        self.themes = sorted(df["themes"].unique())
        self.setup_menu()

    def setup_menu(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        self.menu_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.menu_tab, text="Entrainement")
        self.notebook.add(self.stats_tab, text="Stats")

        frame = ttk.Frame(self.menu_tab, padding=20)
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

        self.build_global_progress()
        
        self.build_stats()

    def build_stats(self):

        theme_width = 150
        bar_width = 450

        legend_row = ttk.Frame(self.stats_tab)
        legend_row.pack(fill="x", pady=10, padx=10)

        ttk.Label(legend_row, text="", width=20).pack(side="left")

        legend_bar = tk.Canvas(legend_row, height=22, width=bar_width)
        legend_bar.pack(side="left")

        legend_bar.create_rectangle(0,0,bar_width/3,22,fill="white",outline="black")
        legend_bar.create_text(bar_width/6,11,text="new")

        legend_bar.create_rectangle(bar_width/3,0,2*bar_width/3,22,fill="orange",outline="")
        legend_bar.create_text(bar_width/2,11,text="wrong")

        legend_bar.create_rectangle(2*bar_width/3,0,bar_width,22,fill="green",outline="")
        legend_bar.create_text(5*bar_width/6,11,text="correct")

        stats = df.groupby(["themes","status"]).size().unstack(fill_value=0)

        for col in ["new","wrong","correct"]:
            if col not in stats.columns:
                stats[col] = 0

        stats["total"] = stats["new"] + stats["wrong"] + stats["correct"]
        stats["wrong_pct"] = stats["wrong"] / stats["total"]

        for theme in stats.sort_values("wrong_pct", ascending=False).index:

            row = ttk.Frame(self.stats_tab)
            row.pack(fill="x", pady=6, padx=10)

            #wrong_pct = stats.loc[theme,"wrong_pct"]

            #if wrong_pct > 0.3:
            #    label = f"⚠ {theme}"
            #elif wrong_pct > 0.1:
            #    label = f"• {theme}"
            #else:
            #    label = f"✓ {theme}"

            #ttk.Label(row, text=label, width=20).pack(side="left")
            ttk.Label(row, text=theme, width=20).pack(side="left")
            bar = tk.Canvas(row, height=22)
            bar.pack(side="left", fill="x", expand=True, padx=10)

            total = stats.loc[theme, "total"]

            if total == 0:
                continue

            new = stats.loc[theme,"new"] / total
            wrong = stats.loc[theme,"wrong"] / total
            correct = stats.loc[theme,"correct"] / total

            width = bar_width

            x0 = 0

            w_new = width * new
            w_wrong = width * wrong
            w_correct = width * correct

            bar.create_rectangle(x0,0,x0+w_new,22,fill="white",outline="black")
            bar.create_text(x0+w_new/2,11,text=f"{int(new*100)}%")

            x0 += w_new

            bar.create_rectangle(x0,0,x0+w_wrong,22,fill="orange",outline="")
            bar.create_text(x0+w_wrong/2,11,text=f"{round(wrong*100)}%")

            x0 += w_wrong

            bar.create_rectangle(x0,0,x0+w_correct,22,fill="green",outline="")
            bar.create_text(x0+w_correct/2,11,text=f"{int(correct*100)}%")

    def build_global_progress(self):

        frame = ttk.Frame(self.menu_tab)
        frame.pack(pady=10)

        ttk.Label(frame, text="Progression globale du vocabulaire",
                font=("Arial", 12, "bold")).pack()

        total = len(df)
        correct = (df["status"] == "correct").sum()

        if total == 0:
            percent = 0
        else:
            percent = correct / total

        bar_width = 400

        canvas = tk.Canvas(frame, width=bar_width, height=25)
        canvas.pack(pady=5)

        filled = bar_width * percent

        canvas.create_rectangle(0,0,filled,25, fill="green")
        canvas.create_rectangle(filled,0,bar_width,25, outline="black")

        canvas.create_text(bar_width/2,12,
                        text=f"{int(percent*100)}%")

        ttk.Label(frame,
                text=f"{correct} / {total} phrases maîtrisées").pack()

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

        # subset = df[df["themes"]==theme].copy()

        today = pd.Timestamp.today()
        self.today = today

        subset = df[
            (df["themes"] == theme) &
            (df["next_review"] <= today)
        ].copy()

        # si aucune carte n'est due aujourd'hui
        if len(subset) == 0:
            subset = df[df["themes"] == theme].copy()

        subset["status"] = subset["status"].fillna("new")

        subset["last_review"] = pd.to_datetime(
            subset["last_review"],
            errors="coerce"
        )

        subset["weight"] = subset.apply(self.compute_weight, axis=1)

        subset["weight"] = subset["weight"].fillna(1)

        if subset["weight"].sum() == 0:
            subset["weight"] = 1

        draw_size = min(len(subset), n * 3)

        # selectionner un échantillon pondéré sans doublons
        draw = subset.sample(
            draw_size,
            weights=subset["weight"],
            replace=True
        ).index.tolist()

        # supprimer doublons en gardant l'ordre
        self.session = list(dict.fromkeys(draw))[:n]

        self.index = 0

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_quiz()

    def setup_quiz(self):
        self.frame = ttk.Frame(self.root, padding=20)
        self.frame.pack()

        self.counter_label = ttk.Label(self.frame, text="", font=("Arial",10))
        self.counter_label.pack(pady=5)

        self.progress = ttk.Progressbar(self.frame, length=400, mode="determinate")
        self.progress.pack(pady=5)

        # carte
        self.card = tk.Frame(
            self.frame,
            bg="white",
            bd=2,
            relief="solid",
            width=500,
            height=220
        )

        self.card.pack(pady=25)
        self.card.pack_propagate(False)

        self.question = tk.Label(
            self.card,
            text="",
            font=("Arial",18,"bold"),
            wraplength=460,
            justify="center",
            bg="white"
        )

        self.question.pack(expand=True)

        self.answer = tk.Label(
            self.card,
            text="",
            font=("Arial",15),
            wraplength=460,
            justify="center",
            fg="gray40",
            bg="white"
        )

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
            text=f"Question {self.index+1} / {len(self.session)}   |   Répétitions prévues : {pending_repeats}"
        )

        self.progress["maximum"] = len(self.session)
        self.progress["value"] = self.index

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

                interval = df.at[self.row_id, "interval"]

                if pd.isna(interval):
                    interval = 1

                interval = min(10, max(1, int(interval) * 2))

                df.at[self.row_id, "interval"] = interval

                df.at[self.row_id, "next_review"] = (
                    pd.Timestamp.now() + pd.Timedelta(days=interval)
                    ).floor("s")

                df.at[self.row_id, "last_review"] = pd.Timestamp.now().floor("s")

            else:
                df.at[self.row_id,"status"] = "wrong"
                df.at[self.row_id, "interval"] = 1
                df.at[self.row_id, "next_review"] = (
                    pd.Timestamp.now() + pd.Timedelta(days=1)
                    ).floor("s")
                df.at[self.row_id, "last_review"] = pd.Timestamp.now().floor("s")

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