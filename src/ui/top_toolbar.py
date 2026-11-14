import tkinter as tk
from tkinter import ttk
from typing import Callable
from src.controllers.simulation_controller import SimulationController


class TopToolbar(ttk.Frame):
    """
    Top toolbar component containing File menu, Run/Reset toggle, and Pause button.
    Strict, academic software aesthetic.
    """
    def __init__(self, parent, controller: SimulationController, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        self.configure(padding=(6, 4))

        # --- File Menu Button ---
        self.file_menu = tk.Menu(self, tearoff=0)
        self.file_menu.add_command(
            label="Сохранить",
            accelerator="Ctrl+S",
            command=lambda: self.controller.file_save(self.winfo_toplevel())
        )
        self.file_menu.add_command(
            label="Сохранить как...",
            accelerator="Ctrl+Shift+S",
            command=lambda: self.controller.file_save_as(self.winfo_toplevel())
        )
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Загрузить...",
            accelerator="Ctrl+O",
            command=lambda: self.controller.file_load(self.winfo_toplevel())
        )

        self.btn_file = ttk.Menubutton(
            self,
            text="Файл ▾",
            menu=self.file_menu,
            direction="below"
        )
        self.btn_file.pack(side=tk.LEFT, padx=(2, 8))

        # Separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=4, pady=2)

        # --- Run / Reset Button ---
        # When idle: "▶ Запуск". When running: "⏹ Сброс"
        self.btn_run_reset = ttk.Button(
            self,
            text="▶ Запуск",
            command=self._on_run_reset_clicked,
            width=12
        )
        self.btn_run_reset.pack(side=tk.LEFT, padx=4)

        # --- Pause Button ---
        self.btn_pause = ttk.Button(
            self,
            text="⏸ Пауза",
            command=self._on_pause_clicked,
            width=12,
            state=tk.DISABLED
        )
        self.btn_pause.pack(side=tk.LEFT, padx=4)

        # Separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        # --- State Indicator Badge ---
        self.lbl_state = ttk.Label(
            self,
            text="Готов к запуску",
            font=("Segoe UI", 9, "italic")
        )
        self.lbl_state.pack(side=tk.LEFT, padx=6)

    def _on_run_reset_clicked(self):
        is_running = self.controller.toggle_run()
        if is_running:
            self.btn_run_reset.configure(text="⏹ Сброс")
            self.btn_pause.configure(state=tk.NORMAL, text="⏸ Пауза")
            self.lbl_state.configure(text="Симуляция: Активна")
        else:
            self.btn_run_reset.configure(text="▶ Запуск")
            self.btn_pause.configure(state=tk.DISABLED, text="⏸ Пауза")
            self.lbl_state.configure(text="Симуляция: Остановлена")

    def _on_pause_clicked(self):
        is_paused = self.controller.toggle_pause()
        if is_paused:
            self.btn_pause.configure(text="▶ Продолжить")
            self.lbl_state.configure(text="Симуляция: Пауза")
        else:
            self.btn_pause.configure(text="⏸ Пауза")
            self.lbl_state.configure(text="Симуляция: Активна")
