import tkinter as tk
from tkinter import ttk
from src.models.scene_objects import SceneModel
from src.controllers.simulation_controller import SimulationController
from src.ui.top_toolbar import TopToolbar
from src.ui.hierarchy_panel import HierarchyPanel
from src.ui.simulation_view import SimulationView
from src.ui.inspector_panel import InspectorPanel


class MainWindow(tk.Tk):
    """
    Main Application Window.
    Provides strict educational laboratory interface layout:
    - Top toolbar: File menu, Run/Reset, Pause.
    - Left sector: Object hierarchy.
    - Center sector: Simulation area (reserved for Max).
    - Right sector: Inspector/settings panel.
    - Bottom: Status bar.
    """
    def __init__(self):
        super().__init__()

        self.title("Физическая симуляция — Лабораторный комплекс")
        self.geometry("1120x720")
        self.minsize(850, 520)

        # Apply strict educational styling
        self._setup_styles()

        # Instantiate Models & Controllers
        self.model = SceneModel()
        self.controller = SimulationController(on_status_change=self.update_status)

        self._build_layout()

        # Connect callbacks
        self.controller.notify_status("Готов к работе. Выберите объект или запустите симуляцию.")

    def _setup_styles(self):
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        # Configure strict educational palette and fonts
        base_font = ("Segoe UI", 9)
        self.style.configure(".", font=base_font)
        self.style.configure("TLabel", font=base_font)
        self.style.configure("TButton", font=base_font, padding=4)
        self.style.configure("TMenubutton", font=base_font, padding=4)
        self.style.configure("TLabelframe.Label", font=("Segoe UI", 9, "bold"))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 8))

    def _build_layout(self):
        # 1. Top Segment: Toolbar
        self.toolbar = TopToolbar(self, controller=self.controller)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X)

        # 2. Bottom Segment: Status Bar
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
            text=f"Объектов: {len(self.model.get_all())}",
            style="Status.TLabel"
        )
        self.lbl_object_count.pack(side=tk.RIGHT, padx=8)

        # 3. Main Workspace: Horizontal PanedWindow (3 Sectors)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Sector: Hierarchy
        self.panel_left = ttk.Frame(self.paned, width=240)
        self.hierarchy_panel = HierarchyPanel(
            self.panel_left,
            model=self.model,
            controller=self.controller,
            on_select_callback=self._on_hierarchy_selection
        )
        self.hierarchy_panel.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_left, weight=1)

        # Center Sector: Simulation View (Max's workspace)
        self.panel_center = ttk.Frame(self.paned, width=580)
        self.simulation_view = SimulationView(self.panel_center)
        self.simulation_view.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_center, weight=3)

        # Right Sector: Inspector / Object Settings
        self.panel_right = ttk.Frame(self.paned, width=280)
        self.inspector_panel = InspectorPanel(
            self.panel_right,
            model=self.model,
            controller=self.controller,
            on_name_changed=self._on_object_renamed
        )
        self.inspector_panel.pack(fill=tk.BOTH, expand=True)
        self.paned.add(self.panel_right, weight=1)

    def _on_hierarchy_selection(self, obj):
        """Dispatches selected object from hierarchy to inspector."""
        self.inspector_panel.load_object(obj)
        self._update_object_count()

    def _on_object_renamed(self, obj_id: str, new_name: str):
        """Synchronizes name modification with hierarchy tree item."""
        self.hierarchy_panel.update_item_name(obj_id, new_name)

    def _update_object_count(self):
        count = len(self.model.get_all())
        self.lbl_object_count.configure(text=f"Объектов в сцене: {count}")

    def update_status(self, message: str):
        self.lbl_status.configure(text=message)
        self._update_object_count()
