import tkinter as tk
from tkinter import filedialog, messagebox

from checker import CATEGORY_OPTIONS, list_standard_difficulties, run_check


class RankingCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AccSaber Ranking Checker")
        self.root.geometry("900x700")
        self.root.minsize(760, 560)
        self.root.resizable(True, True)

        self.colors = {
            "bg": "#12121d",
            "panel": "#1a1b28",
            "text": "#f7f4ee",
            "muted": "#c7bca8",
            "border": "#4a3216",
            "input": "#221d16",
            "button": "#f0a41f",
            "button_text": "#16120d",
            "button_active": "#ffbf45",
            "input_border": "#8f5a17",
            "accent": "#ffbe3b",
        }

        self.mapset_path_var = tk.StringVar()
        self.difficulty_var = tk.StringVar()
        self.category_var = tk.StringVar(value=CATEGORY_OPTIONS[0])
        self.status_var = tk.StringVar(value="Choose a map folder to begin.")

        self.root.configure(bg=self.colors["bg"])
        self._build_ui()

    def _build_ui(self):
        container = tk.Frame(self.root, bg=self.colors["bg"], padx=16, pady=16)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="AccSaber Ranking Checker",
            font=("Helvetica", 20, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["accent"],
            anchor="w",
        )
        title.pack(fill="x")

        subtitle = tk.Label(
            container,
            text="Choose a map folder, then select the difficulty and criteria category.",
            font=("Helvetica", 11),
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            anchor="w",
            pady=8,
        )
        subtitle.pack(fill="x")

        form = tk.LabelFrame(
            container,
            text="Map Selection",
            font=("Helvetica", 12, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            bd=1,
            relief="solid",
            padx=12,
            pady=12,
        )
        form.pack(fill="x", pady=(8, 12))
        form.grid_columnconfigure(1, weight=1)

        tk.Label(
            form,
            text="Map folder",
            bg=self.colors["panel"],
            fg=self.colors["text"],
        ).grid(row=0, column=0, sticky="w")

        folder_entry = tk.Entry(
            form,
            textvariable=self.mapset_path_var,
            bg=self.colors["input"],
            fg=self.colors["text"],
            readonlybackground=self.colors["input"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors["input_border"],
            highlightcolor=self.colors["input_border"],
        )
        folder_entry.grid(row=0, column=1, sticky="ew", padx=8)
        folder_entry.configure(state="readonly")

        tk.Button(
            form,
            text="Choose Folder",
            command=self.choose_folder,
            bg=self.colors["button"],
            fg=self.colors["button_text"],
            activebackground=self.colors["button_active"],
            activeforeground=self.colors["button_text"],
            relief="flat",
            padx=12,
            pady=6,
        ).grid(row=0, column=2, sticky="ew")

        tk.Label(
            form,
            text="Difficulty",
            bg=self.colors["panel"],
            fg=self.colors["text"],
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))

        self.difficulty_menu = tk.OptionMenu(form, self.difficulty_var, "")
        self._style_option_menu(self.difficulty_menu)
        self.difficulty_menu.grid(row=1, column=1, sticky="w", padx=8, pady=(12, 0))

        tk.Label(
            form,
            text="Criteria category",
            bg=self.colors["panel"],
            fg=self.colors["text"],
        ).grid(row=2, column=0, sticky="w", pady=(12, 0))

        self.category_menu = tk.OptionMenu(form, self.category_var, *CATEGORY_OPTIONS)
        self._style_option_menu(self.category_menu)
        self.category_menu.grid(row=2, column=1, sticky="w", padx=8, pady=(12, 0))

        self.run_button = tk.Button(
            container,
            text="Run Criteria Check",
            command=self.run_checker,
            bg=self.colors["button"],
            fg=self.colors["button_text"],
            activebackground=self.colors["button_active"],
            activeforeground=self.colors["button_text"],
            relief="flat",
            padx=12,
            pady=8,
        )
        self.run_button.pack(anchor="w", pady=(0, 12))

        status = tk.Label(
            container,
            textvariable=self.status_var,
            bg=self.colors["bg"],
            fg=self.colors["text"],
            anchor="w",
            justify="left",
        )
        status.pack(fill="x", pady=(0, 8))

        output_frame = tk.Frame(
            container,
            bg=self.colors["panel"],
            bd=3,
            relief="solid",
        )
        output_frame.pack(fill="both", expand=True)
        output_frame.grid_rowconfigure(0, weight=1)
        output_frame.grid_columnconfigure(0, weight=1)

        self.output_text = tk.Text(
            output_frame,
            bg=self.colors["input"],
            fg=self.colors["text"],
            insertbackground=self.colors["text"],
            relief="solid",
            bd=1,
            wrap="word",
            padx=12,
            pady=12,
            highlightthickness=1,
            highlightbackground=self.colors["input_border"],
            highlightcolor=self.colors["input_border"],
            state="disabled",
        )
        self.output_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(output_frame, command=self.output_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output_text.configure(yscrollcommand=scrollbar.set)

    def _style_option_menu(self, widget):
        widget.configure(
            bg=self.colors["input"],
            fg=self.colors["text"],
            activebackground=self.colors["input"],
            activeforeground=self.colors["text"],
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors["input_border"],
            highlightcolor=self.colors["input_border"],
            padx=8,
        )
        widget["menu"].configure(
            bg=self.colors["panel"],
            fg=self.colors["text"],
            activebackground=self.colors["button"],
            activeforeground=self.colors["button_text"],
        )

    def _set_difficulty_options(self, difficulties):
        menu = self.difficulty_menu["menu"]
        menu.delete(0, "end")

        if not difficulties:
            self.difficulty_var.set("")
            menu.add_command(label="", command=lambda: self.difficulty_var.set(""))
            return

        for difficulty in difficulties:
            menu.add_command(
                label=difficulty,
                command=lambda value=difficulty: self.difficulty_var.set(value),
            )
        self.difficulty_var.set(difficulties[0])

    def choose_folder(self):
        selected_path = filedialog.askdirectory(title="Choose Beat Saber map folder")
        if not selected_path:
            return

        self.mapset_path_var.set(selected_path)
        self.status_var.set("Loading difficulties...")
        self._set_output("")
        self.root.update_idletasks()

        try:
            difficulties = list_standard_difficulties(selected_path)
        except Exception as exc:
            self._set_difficulty_options([])
            self.status_var.set("Could not read difficulties from that folder.")
            self._set_output(f"Error loading map folder:\n{exc}")
            return

        self._set_difficulty_options(difficulties)
        if difficulties:
            self.status_var.set("Map loaded. Choose difficulty and category, then run the check.")
            self._set_output(
                "Loaded map folder successfully.\n\n"
                f"Available difficulties: {', '.join(difficulties)}"
            )
        else:
            self.status_var.set("No Standard difficulties found in that folder.")
            self._set_output("No Standard difficulties were found in the selected map folder.")

    def run_checker(self):
        mapset_path = self.mapset_path_var.get().strip()
        difficulty = self.difficulty_var.get().strip()
        category = self.category_var.get().strip()

        if not mapset_path:
            messagebox.showerror("Missing folder", "Choose a map folder first.")
            return
        if not difficulty:
            messagebox.showerror("Missing difficulty", "Choose a difficulty first.")
            return
        if not category:
            messagebox.showerror("Missing category", "Choose a criteria category first.")
            return

        self.run_button.configure(state="disabled")
        self.status_var.set("Running criteria check...")
        self.root.update_idletasks()

        try:
            output = run_check(mapset_path, difficulty, category)
        except Exception as exc:
            self.status_var.set("The check failed.")
            self._set_output(f"Error:\n{exc}")
            messagebox.showerror("Criteria Check Error", str(exc))
        else:
            lines = [output["summary"], ""]
            if output["logs"]:
                lines.append("Issues found:")
                lines.extend(output["logs"])
            else:
                lines.append("No criteria issues were found.")
            self._set_output("\n".join(lines))
            self.status_var.set("Check complete.")
        finally:
            self.run_button.configure(state="normal")

    def _set_output(self, text):
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.configure(state="disabled")
        self.output_text.yview_moveto(0)
        self.root.update_idletasks()


def main():
    root = tk.Tk()
    RankingCheckerApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
