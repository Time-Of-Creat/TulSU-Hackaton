import tkinter as tk
from tkinter import ttk
from typing import Optional
from source.view.models.scene_objects import SceneModel
from source.view.controllers.simulation_controller import SimulationController
from source.view.ui.top_toolbar import TopToolbar
from source.view.ui.hierarchy_panel import HierarchyPanel
from source.view.ui.simulation_view import SimulationView
from source.view.ui.inspector_panel import InspectorPanel


class MainWindow(tk.Tk):
    """
    Главное окно приложения с панелью инструментов,
    иерархией объектов, симуляцией, инспектором и строкой состояния.
    """
    def __init__(self, controller: Optional[SimulationController] = None):
        super().__init__()

        self.title("Физическая симуляция — Лабораторный комплекс")
        self.geometry("1120x720")
        self.minsize(850, 520)

        self._setup_styles()

        if controller is not None:
            self.controller = controller
            self.controller.set_status_callback(self.update_status)
        else:
            self.controller = SimulationController(on_status_change=self.update_status)

        self.model = SceneModel(backend=getattr(self.controller, "backend", None))
        self.controller.on_scene_changed = self._on_scene_reloaded

        self._build_layout()
        self._bind_shortcuts()

        self.controller.notify_status("Готов к работе. Выберите объект или запустите симуляцию.")

    def _setup_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        base_font = ("Segoe UI", 9)
        self.style.configure(".", font=base_font)
        self.style.configure("TLabel", font=base_font)
        self.style.configure("TButton", font=base_font, padding=4)
        self.style.configure("TMenubutton", font=base_font, padding=4)
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 8))

    def _bind_shortcuts(self):
        self.bind_all("<Control-s>", lambda e: self.controller.file_save(self))
        self.bind_all("<Control-S>", lambda e: self.controller.file_save_as(self))
        self.bind_all("<Control-o>", lambda e: self.controller.file_load(self))

    def _build_layout(self):
        self.toolbar = TopToolbar(self, controller=self.controller)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X)

        self.status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(6, 3))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_status = ttk.Label(
            self.status_bar,
            text="Инициализация...",
            style="Status.TLabel"
        )
        self.lbl_status.pack(side=tk.LEFT)

        self.lbl_object_count = ttk.Label(
            self.status_bar,
            text=f"Объектов в сцене: {len(self.model.get_all())}",
            style="Status.TLabel"
        )
        self.lbl_object_count.pack(side=tk.RIGHT, padx=8)

        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.panel_left = ttk.Frame(self.paned, width=240)
        self.hierarchy_panel = HierarchyPanel(
            self.panel_left,
            model=self.model,
            controller=self.controller,
            on_select_callback=self._on_hierarchy_selection
        )
        self.hierarchy_panel.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_left, weight=1)

        self.panel_center = ttk.Frame(self.paned, width=580)
        self.simulation_view = SimulationView(
            self.panel_center,
            backend=getattr(self.controller, "backend", None)
        )
        self.simulation_view.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_center, weight=3)

        self.panel_right = ttk.Frame(self.paned, width=280)
        self.inspector_panel = InspectorPanel(
            self.panel_right,
            model=self.model,
            controller=self.controller,
            on_name_changed=self._on_object_renamed
        )
        self.inspector_panel.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_right, weight=1)

        first_sel = self.hierarchy_panel.tree.selection()
        if first_sel:
            self.inspector_panel.load_object(self.model.get_by_id(first_sel[0]))

    def _on_hierarchy_selection(self, obj):
        if hasattr(self, "inspector_panel"):
            self.inspector_panel.load_object(obj)
        self._update_object_count()

    def _on_object_renamed(self, obj_id: str, new_name: str):
        self.hierarchy_panel.update_item_name(obj_id, new_name)

    def _on_scene_reloaded(self):
        self.hierarchy_panel.refresh_tree()
        self._update_object_count()
        if hasattr(self, "toolbar"):
            self.toolbar.btn_run_reset.configure(text="▶ Запуск")
            self.toolbar.btn_pause.configure(state=tk.DISABLED, text="⏸ Пауза")
            self.toolbar.lbl_state.configure(text="Симуляция: Загружена")

    def _update_object_count(self):
        count = len(self.model.get_all())
        self.lbl_object_count.configure(text=f"Объектов в сцене: {count}")

    def update_status(self, message: str):
        self.lbl_status.configure(text=message)
        self._update_object_count()
