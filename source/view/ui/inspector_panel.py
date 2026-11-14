import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, Any
from source.view.models.scene_objects import SceneModel, SceneObject
from source.view.controllers.simulation_controller import SimulationController


class InspectorPanel(ttk.Frame):
    """
    Правая панель свойств выбранного объекта.
    Отображает и редактирует свойства объекта, а также обновляет
    динамические параметры (координаты, скорость, ускорение) в реальном времени.
    """
    def __init__(self, parent, model: SceneModel, controller: SimulationController,
                 on_name_changed: Callable[[str, str], None], *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.model = model
        self.controller = controller
        self.on_name_changed = on_name_changed
        self.current_obj_id: Optional[str] = None
        self._fields: Dict[str, Dict[str, Any]] = {}

        self._build_ui()
        self._start_live_loop()

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
        self.current_obj_id = None
        self._clear_content()
        self._fields.clear()

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

        self.current_obj_id = obj.id
        self._clear_content()
        self._fields.clear()

        type_str = "Планета / Тело" if getattr(obj, "obj_type", "") == "planet" else "Координатная система"
        summary_frame = ttk.LabelFrame(self.content_frame, text="Идентификация", padding=6)
        summary_frame.pack(fill=tk.X, padx=6, pady=(4, 6))

        self.lbl_title_name = ttk.Label(
            summary_frame,
            text=f"{getattr(obj, 'icon', '📦')}  {obj.name}",
            font=("Segoe UI", 10, "bold")
        )
        self.lbl_title_name.pack(anchor=tk.W)

        ttk.Label(
            summary_frame,
            text=f"Тип: {type_str} | ID: {obj.id}",
            font=("Segoe UI", 8)
        ).pack(anchor=tk.W, pady=(2, 0))

        if getattr(obj, "obj_type", "") == "plane":
            self._render_plane_properties(obj)
        else:
            self._render_planet_properties(obj)

    def _render_plane_properties(self, obj: SceneObject):
        grp_gen = ttk.LabelFrame(self.content_frame, text="Параметры координатной системы", padding=6)
        grp_gen.pack(fill=tk.X, padx=6, pady=4)

        self._add_text_field(grp_gen, "Имя системы:", "name", lambda o: getattr(o, "name", ""))
        self._add_number_field(grp_gen, "Шаг сетки (м):", "grid_step", lambda o: getattr(o, "grid_step", 10.0))
        self._add_number_field(grp_gen, "Размер сетки (м):", "grid_size", lambda o: getattr(o, "grid_size", 100.0))
        self._add_text_field(grp_gen, "Цвет линий:", "line_color", lambda o: getattr(o, "line_color", "#7A8288"))
        self._add_check_field(grp_gen, "Отображать систему", "is_visible", lambda o: bool(getattr(o, "is_visible", True)))

        grp_pos = ttk.LabelFrame(self.content_frame, text="Позиция (X, Y) [м]", padding=6)
        grp_pos.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_pos, "Позиция X (м):", "pos_x", lambda o: getattr(getattr(o, "local_position", None), "x", 0.0))
        self._add_number_field(grp_pos, "Позиция Y (м):", "pos_y", lambda o: getattr(getattr(o, "local_position", None), "y", 0.0))

    def _render_planet_properties(self, obj: SceneObject):
        grp_gen = ttk.LabelFrame(self.content_frame, text="Основные свойства", padding=6)
        grp_gen.pack(fill=tk.X, padx=6, pady=4)

        self._add_text_field(grp_gen, "Имя объекта:", "name", lambda o: getattr(o, "name", ""))
        self._add_text_field(grp_gen, "Цвет (HEX):", "color", lambda o: getattr(o, "color", "#4A90E2"))
        self._add_check_field(grp_gen, "Статичный объект", "is_fixed", lambda o: bool(getattr(o, "is_fixed", False)))

        grp_phys = ttk.LabelFrame(self.content_frame, text="Физические параметры", padding=6)
        grp_phys.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_phys, "Масса (кг):", "mass", lambda o: getattr(o, "mass", 1.0))
        self._add_number_field(grp_phys, "Плотность (кг/м³):", "density", lambda o: getattr(o, "density", 1.0))
        self._add_readonly_field(grp_phys, "Радиус (м):", lambda o: f"{o.calculate_radius():.2f} м" if hasattr(o, "calculate_radius") else "—")

        grp_pos = ttk.LabelFrame(self.content_frame, text="Координаты (X, Y) [м]", padding=6)
        grp_pos.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_pos, "Позиция X (м):", "pos_x", lambda o: getattr(getattr(o, "local_position", None), "x", 0.0))
        self._add_number_field(grp_pos, "Позиция Y (м):", "pos_y", lambda o: getattr(getattr(o, "local_position", None), "y", 0.0))

        grp_vel = ttk.LabelFrame(self.content_frame, text="Скорость (Vx, Vy) [м/с]", padding=6)
        grp_vel.pack(fill=tk.X, padx=6, pady=4)

        self._add_number_field(grp_vel, "Скорость Vx (м/с):", "vel_x", lambda o: getattr(getattr(o, "velocity", None), "x", 0.0))
        self._add_number_field(grp_vel, "Скорость Vy (м/с):", "vel_y", lambda o: getattr(getattr(o, "velocity", None), "y", 0.0))

        grp_mon = ttk.LabelFrame(self.content_frame, text="Динамика (Мониторинг)", padding=6)
        grp_mon.pack(fill=tk.X, padx=6, pady=4)

        self._add_readonly_field(grp_mon, "Ускорение:", lambda o: f"({o.acceleration.x:.3f}, {o.acceleration.y:.3f}) м/с²" if hasattr(o, "acceleration") else "—")
        self._add_readonly_field(grp_mon, "Сила F:", lambda o: f"({o.F.x:.2e}, {o.F.y:.2e}) Н" if hasattr(o, "F") else "—")

    def _add_text_field(self, parent, label_text: str, key: str, getter: Callable[[Any], Any]):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
        init_val = str(getter(obj)) if obj else ""
        var = tk.StringVar(value=init_val)
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        entry.bind("<FocusOut>", lambda e: self._on_field_commit(key, var.get()))
        entry.bind("<Return>", lambda e: self._on_field_commit(key, var.get()))
        self._fields[key] = {"widget": entry, "var": var, "getter": getter, "type": "text"}

    def _add_number_field(self, parent, label_text: str, key: str, getter: Callable[[Any], Any]):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
        init_num = getter(obj) if obj else 0.0
        var = tk.StringVar(value=self._format_number(init_num))
        entry = ttk.Entry(row, textvariable=var)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        def commit():
            val_str = var.get().strip()
            try:
                numeric_val = float(val_str)
                self._on_field_commit(key, numeric_val)
            except ValueError:
                # restore previous value if invalid
                cur_obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
                if cur_obj:
                    var.set(self._format_number(getter(cur_obj)))

        entry.bind("<FocusOut>", lambda e: commit())
        entry.bind("<Return>", lambda e: commit())
        self._fields[key] = {"widget": entry, "var": var, "getter": getter, "type": "number"}

    def _add_combobox_field(self, parent, label_text: str, key: str, values: list, getter: Callable[[Any], Any]):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
        init_val = str(getter(obj)) if obj else values[0]
        cb = ttk.Combobox(row, values=values, state="readonly")
        cb.set(init_val)
        cb.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        cb.bind("<<ComboboxSelected>>", lambda e: self._on_field_commit(key, cb.get()))
        self._fields[key] = {"widget": cb, "var": None, "getter": getter, "type": "combo"}

    def _add_check_field(self, parent, label_text: str, key: str, getter: Callable[[Any], Any]):
        obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
        init_val = bool(getter(obj)) if obj else False
        var = tk.BooleanVar(value=init_val)
        chk = ttk.Checkbutton(
            parent,
            text=label_text,
            variable=var,
            command=lambda: self._on_field_commit(key, var.get())
        )
        chk.pack(anchor=tk.W, pady=3)
        self._fields[key] = {"widget": chk, "var": var, "getter": getter, "type": "check"}

    def _add_readonly_field(self, parent, label_text: str, getter: Callable[[Any], Any]):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=2)
        ttk.Label(row, text=label_text, width=16, anchor=tk.W).pack(side=tk.LEFT)

        obj = self.model.get_by_id(self.current_obj_id) if self.current_obj_id else None
        val_str = str(getter(obj)) if obj else "—"
        lbl_val = ttk.Label(row, text=val_str, anchor=tk.E, font=("Segoe UI", 9, "bold"))
        lbl_val.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        self._fields[f"ro_{label_text}"] = {"widget": lbl_val, "var": None, "getter": getter, "type": "readonly"}

    def _start_live_loop(self):
        self._update_live_values()
        self.after(50, self._start_live_loop)

    def _update_live_values(self):
        if not self.current_obj_id:
            return

        obj = self.model.get_by_id(self.current_obj_id)
        if not obj:
            self.show_empty()
            return

        try:
            focused = self.focus_get()
        except Exception:
            focused = None

        for key, info in list(self._fields.items()):
            w = info["widget"]
            # Если поле сейчас редактируется пользователем, не перезаписываем его значение
            if w == focused:
                continue

            getter = info.get("getter")
            if not getter:
                continue

            try:
                raw_val = getter(obj)
            except Exception:
                continue

            ftype = info.get("type")
            var = info.get("var")

            if ftype == "readonly":
                w.configure(text=str(raw_val))
            elif ftype == "number":
                try:
                    num = float(raw_val)
                    cur_str = var.get().strip()
                    try:
                        cur_f = float(cur_str)
                        if abs(cur_f - num) > 1e-4:
                            var.set(self._format_number(num))
                    except ValueError:
                        var.set(self._format_number(num))
                except (ValueError, TypeError):
                    var.set(str(raw_val))
            elif ftype == "text":
                s = str(raw_val)
                if var.get() != s:
                    var.set(s)
            elif ftype == "check":
                b = bool(raw_val)
                if var.get() != b:
                    var.set(b)
            elif ftype == "combo":
                s = str(raw_val)
                if w.get() != s:
                    w.set(s)

    @staticmethod
    def _format_number(value: float) -> str:
        try:
            num = float(value)
            if abs(num) >= 10000 or (0 < abs(num) < 0.01):
                return f"{num:.3e}"
            if num.is_integer():
                return f"{num:.1f}"
            return f"{num:.3f}"
        except (ValueError, TypeError):
            return str(value)

    def _on_field_commit(self, key: str, value: Any):
        if not self.current_obj_id:
            return

        obj = self.model.get_by_id(self.current_obj_id)
        if not obj:
            return

        success = self.model.update_property(obj.id, key, value)
        if success:
            self.controller.on_property_changed(obj.id, key, value)
            if key in self._fields:
                var = self._fields[key].get("var")
                if var is not None and self._fields[key].get("type") == "number":
                    var.set(self._format_number(value))
                elif var is not None:
                    var.set(str(value))

            if key == "name":
                new_name = str(value)
                self.on_name_changed(obj.id, new_name)
                if hasattr(self, "lbl_title_name"):
                    icon = getattr(obj, "icon", "📦")
                    self.lbl_title_name.configure(text=f"{icon}  {new_name}")

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
