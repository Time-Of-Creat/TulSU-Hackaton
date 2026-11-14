import tkinter as tk
from tkinter import ttk


class SimulationView(ttk.Frame):
    """
    Center sector: Simulation Viewport placeholder.
    Reserved for Max's physics simulation engine (Pygame, OpenGL, or Canvas).
    """
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self._build_ui()

    def _build_ui(self):
        # Viewport Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        lbl_title = ttk.Label(
            header_frame,
            text="Сектор симуляции",
            font=("Segoe UI", 9, "bold")
        )
        lbl_title.pack(side=tk.LEFT)

        lbl_res = ttk.Label(
            header_frame,
            text="Статус: Ожидание модуля симуляции",
            font=("Segoe UI", 8, "italic")
        )
        lbl_res.pack(side=tk.RIGHT)

        # Technical canvas placeholder
        self.canvas = tk.Canvas(
            self,
            background="#1e1e24",
            highlightthickness=1,
            highlightbackground="#3a3a44"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)

        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Draws subtle educational technical grid and placeholder badge."""
        w = event.width
        h = event.height
        self.canvas.delete("all")

        # Technical background grid lines (subtle dark theme)
        step = 40
        grid_color = "#282832"
        for x in range(0, w, step):
            self.canvas.create_line(x, 0, x, h, fill=grid_color)
        for y in range(0, h, step):
            self.canvas.create_line(0, y, w, y, fill=grid_color)

        # Center axes
        cx, cy = w // 2, h // 2
        axis_color = "#3d4251"
        self.canvas.create_line(cx, 0, cx, h, fill=axis_color, dash=(4, 4))
        self.canvas.create_line(0, cy, w, cy, fill=axis_color, dash=(4, 4))

        # Placeholder Banner
        self.canvas.create_rectangle(
            cx - 180, cy - 35, cx + 180, cy + 35,
            fill="#252530", outline="#4f5263", width=1
        )
        self.canvas.create_text(
            cx, cy - 10,
            text="ОБЛАСТЬ СИМУЛЯЦИИ",
            fill="#e0e0e0",
            font=("Segoe UI", 11, "bold")
        )
        self.canvas.create_text(
            cx, cy + 12,
            text="(Резерв под модуль визуализации / Работа Макса)",
            fill="#9a9aa8",
            font=("Segoe UI", 8)
        )

    # --- Hooks for Max ---
    def get_render_canvas(self) -> tk.Canvas:
        """Returns the Tkinter canvas widget for direct drawing."""
        return self.canvas

    def get_container_id(self) -> int:
        """Returns OS window handle (HWND/XID) for embedding external engines like Pygame."""
        return self.canvas.winfo_id()
