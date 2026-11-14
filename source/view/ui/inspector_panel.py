import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any
from source.view.models.scene_objects import SceneModel, SceneObject
from source.view.controllers.simulation_controller import SimulationController


class InspectorPanel(ttk.Frame):
    """
    Правая панель свойств выбранного объекта.
    Показывает редактируемые поля объекта из иерархии.
    """
    def __init__(self, parent, model: SceneModel, controller: SimulationController,
                 on_name_changed: Callable[[str, str], None], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.controller = controller
        self.on_name_changed = on_name_changed
        self.current_obj: Optional[SceneObject] = None
        self._entries: Dict[str, Any] = {}

        self._build_ui()

    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=4, pady=(4, 2))

        lbl_title = ttk.Label(
            header_frame,
            text="Свойства объекта",
            font=("Segoe UI", 9, "bold")
        )
        lbl_title.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        self.content_frame = ttk.Frame(self.canvas)

        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=2)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=2)

        self.show_empty()

    def show_empty(self):
        self.current_obj = None
        self._clear_content()

        lbl_placeholder = ttk.Label(
            self.content_frame,
            text="Выберите объект\nв левом секторе для\nредактирования свойств",
            justify=tk.CENTER,
            font=("Segoe UI", 9, "italic")
        )
        lbl_placeholder.pack(pady=40, padx=10, fill=tk.X)

    def load_object(self, obj: Optional[SceneObject]):
        if not obj:
            self.show_empty()
            return

        self.current_obj = obj
        self._clear_content()
        self._entries.clear()

        type_str = "Планета / Тело" if obj.obj_type == "planet" else "Координатная плоскость"
        summary_frame = ttk.LabelFrame(self.content_frame, text="Идентификация", padding=6)
        summary_frame.pack(fill=tk.X, padx=6, pady=(4, 6))

        ttk.Label(
            summary_frame,
            text=f"{obj.icon}  {obj.name}",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W)

        ttk.Label(
            summary_frame,
            text=f"Тип: {type_str} | ID: {obj.id}",
            font=("Segoe UI", 8)
        ).pack(anchor=tk.W, pady=(2, 0))

        if obj.obj_type == "plane":
            self._render_plane_properties(obj)
        else:
            self._render_planet_properties(obj)

    def _render_plane_properties(self, obj: SceneObject):
        p = obj.properties

        grp_gen = ttk.LabelFrame(self.content_frame, text="Параметры сетки", padding=6)
        grp_gen.pack(fill=tk.X, padx=6, pady=4)

        self._add_text_field(grp_gen, "Имя плоскости:", "name", str(p.get("name", "")))
        self._add_combobox_field(grp_gen, "Проекция:", "orientation", ["XY", "XZ", "YZ"], str(p.get("orientation", "XY")))
        self._add_number_field(grp_gen, "Шаг сетки:", "grid_step", p.get("grid_step", 10.0))
        self._add_number_field(grp_gen, "Размер сетки:", "grid_size", p.get("grid_size", 100.0))
        self._add_text_field(grp_gen, "Цвет линий:", "line_color", str(p.get("line_color", "#7A8288")))
        self._add_check_field(grp_gen, "Отображать плоскость", "is_visible", bool(p.get("is_visible", True)))

    def _render_planet_properties(self, obj: SceneObject):
        p = obj.properties

        grp_gen = ttk.LabelFrame(self.content_frame, text="Основные свойства", padding=6)
        grp_gen.pack(fill=tk.X, padx=6, pady=4)

        self._add_text_field(grp_gen, "Имя объекта:", "name", str(p.get("name", "")))
        self._add_text_field(grp_gen, "Цвет (HEX):", "color", str(p.get("color", "#4A90E2")))
        self._add_check_field(grp_gen, "Статичный объект (неподвижен)", "is_fixed", bool(p.get("is_fixed", False)))

        grp_phys = ttk.LabelFrame(self.content_frame, text="Физические параметры", padding=6)
        grp_phys.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_phys, "Масса (кг):", "mass", p.get("mass", 1.0))
        self._add_number_field(grp_phys, "Радиус (км):", "radius", p.get("radius", 1.0))

        grp_pos = ttk.LabelFrame(self.content_frame, text="Координаты (X, Y, Z)", padding=6)
        grp_pos.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_pos, "Позиция X:", "pos_x", p.get("pos_x", 0.0))
        self._add_number_field(grp_pos, "Позиция Y:", "pos_y", p.get("pos_y", 0.0))
        self._add_number_field(grp_pos, "Позиция Z:", "pos_z", p.get("pos_z", 0.0))

        grp_vel = ttk.LabelFrame(self.content_frame, text="Скорость (Vx, Vy, Vz)", padding=6)
        grp_vel.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_vel, "Скорость Vx:", "vel_x", p.get("vel_x", 0.0))
        self._add_number_field(grp_vel, "Скорость Vy:", "vel_y", p.get("vel_y", 0.0))
        self._add_number_field(grp_vel, "Скорость Vz:", "vel_z", p.get("vel_z", 0.0))

    def _add_text_field(self, parent, label_text: str, key: str, default_val: str):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        var = tk.StringVar(value=default_val)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        entry.bind("<FocusOut>", lambda e: self._on_field_commit(key, var.get()))
        entry.bind("<Return>", lambda e: self._on_field_commit(key, var.get()))
        self._entries[key] = var

    def _add_number_field(self, parent, label_text: str, key: str, default_val: Any):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        var = tk.StringVar(value=str(default_val))
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        def commit():
            val_str = var.get().strip()
            try:
                numeric_val = float(val_str)
            except ValueError:
                numeric_val = val_str
            self._on_field_commit(key, numeric_val)

        entry.bind("<FocusOut>", lambda e: commit())
        entry.bind("<Return>", lambda e: commit())
        self._entries[key] = var

    def _add_combobox_field(self, parent, label_text: str, key: str, values: list, default_val: str):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        cb = ttk.Combobox(row, values=values, state="readonly")
        cb.set(default_val)
        cb.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        cb.bind("<<ComboboxSelected>>", lambda e: self._on_field_commit(key, cb.get()))
        self._entries[key] = cb

    def _add_check_field(self, parent, label_text: str, key: str, default_val: bool):
        var = tk.BooleanVar(value=default_val)
        chk = ttk.Checkbutton(
            parent,
            text=label_text,
            variable=var,
            command=lambda: self._on_field_commit(key, var.get())
        )
        chk.pack(anchor=tk.W, pady=3)
        self._entries[key] = var

    def _on_field_commit(self, key: str, value: Any):
        if not self.current_obj:
            return

        self.model.update_property(self.current_obj.id, key, value)
        self.controller.on_property_changed(self.current_obj.id, key, value)

        if key == "name":
            self.on_name_changed(self.current_obj.id, str(value))

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
